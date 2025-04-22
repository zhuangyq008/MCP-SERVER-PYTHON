from datetime import datetime
from typing import Any, Dict, List, Optional
import os
import time

import boto3
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("aws_s3table_query")

# Global Athena configuration
# 从环境变量读取配置
athena_config = {
    "catalog": os.getenv("ATHENA_CATALOG"),
    "database": os.getenv("ATHENA_DATABASE"),
    "table": os.getenv("ATHENA_TABLE"),
    "output_location": os.getenv("ATHENA_OUTPUT_LOCATION")
}

aws_config = {
    "region": os.getenv("AWS_REGION", "us-east-1")
}

athena_client = None

def initialize():
        global athena_config, aws_config, athena_client
        
        # Validate required environment variables
        required_vars = [
            ("ATHENA_DATABASE", athena_config["database"]),
            ("ATHENA_TABLE", athena_config["table"]),
            ("ATHENA_OUTPUT_LOCATION", athena_config["output_location"])
        ]
        
        missing_vars = [var_name for var_name, var_value in required_vars if var_value is None]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Initialize Athena client
        athena_client = boto3.client('athena', region_name=aws_config['region'])


# 从环境变量初始化athena连接
initialize()

def wait_for_query_completion(query_execution_id: str) -> bool:
    """Wait for an Athena query to complete, returning True if successful."""
    while True:
        response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        state = response['QueryExecution']['Status']['State']
        
        if state == 'SUCCEEDED':
            return True
        elif state in ['FAILED', 'CANCELLED']:
            raise Exception(f"Query {query_execution_id} failed with state {state}")
        
        time.sleep(1)  # Wait before checking again

def get_query_results(query_execution_id: str) -> List[Dict[str, Any]]:
    """Fetch and process query results from Athena."""
    results = []
    paginator = athena_client.get_paginator('get_query_results')
    
    try:
        for page in paginator.paginate(QueryExecutionId=query_execution_id):
            if not results:  # First page, get column info
                columns = [col['Name'] for col in page['ResultSet']['ResultSetMetadata']['ColumnInfo']]
            
            # Process each row (skip header row in first page)
            start_idx = 1 if not results else 0
            for row in page['ResultSet']['Rows'][start_idx:]:
                values = [field.get('VarCharValue', None) for field in row['Data']]
                results.append(dict(zip(columns, values)))
                
    except Exception as e:
        raise Exception(f"Error fetching query results: {str(e)}")
        
    return results

def execute_query(query: str) -> List[Dict[str, Any]]:
    """Execute an Athena query and return the results."""
    try:
        # Start query execution
        response = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={
                'Database': athena_config['database'],
                'Catalog': athena_config['catalog'] if athena_config['catalog'] else 'AwsDataCatalog'
            },
            ResultConfiguration={
                'OutputLocation': athena_config['output_location']
            }
        )
        
        query_execution_id = response['QueryExecutionId']
        
        # Wait for query completion
        if wait_for_query_completion(query_execution_id):
            return get_query_results(query_execution_id)
        
        return []
        
    except Exception as e:
        raise Exception(f"Error executing query: {str(e)}")



def build_where_clause(
                          start_time: Optional[str] = None,
                          end_time: Optional[str] = None,
                          bucket: Optional[str] = None,
                          record_type: Optional[str] = None,
                          storage_class: Optional[str] = None,
                          source_ip_address: Optional[str] = None) -> str:
        conditions = []
        
        if start_time:
            conditions.append(f"record_timestamp >= '{start_time}'")
        if end_time:
            conditions.append(f"record_timestamp <= '{end_time}'")
        if bucket:
            conditions.append(f"bucket = '{bucket}'")
        if record_type:
            conditions.append(f"record_type = '{record_type}'")
        if storage_class:
            conditions.append(f"storage_class = '{storage_class}'")
        if source_ip_address:
            conditions.append(f"source_ip_address = '{source_ip_address}'")
            
        if conditions:
            return "WHERE " + " AND ".join(conditions)
        return ""

@mcp.tool()
async def query_record(
                    start_time: Optional[str] = None,
                    end_time: Optional[str] = None,
                    bucket: Optional[str] = None,
                    record_type: Optional[str] = None,
                    storage_class: Optional[str] = None,
                    source_ip_address: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query S3 object records based on specified conditions.
        
        Args:
            start_time: Start time for record_timestamp range (ISO format)
            end_time: End time for record_timestamp range (ISO format)
            bucket: S3 bucket name
            record_type: Type of record
            storage_class: S3 storage class
            source_ip_address: Source IP address
            
        Returns:
            List of matching records
        """
        where_clause = build_where_clause(
            start_time, end_time, bucket, record_type, 
            storage_class, source_ip_address
        )
        
        query = f"""
        SELECT bucket, key, sequence_number, record_type, 
               record_timestamp, size, last_modified_date,
               e_tag, storage_class, is_multipart,
               encryption_status, is_bucket_key_enabled,
               kms_key_arn, checksum_algorithm, object_tags,
               user_metadata, requester, source_ip_address,
               request_id
        FROM {athena_config['database']}.{athena_config['table']}
        {where_clause}
        """
        print(query)
        return execute_query(query)

@mcp.tool()
async def query_statistics(
                        group_by: List[str],
                        start_time: Optional[str] = None,
                        end_time: Optional[str] = None,
                        bucket: Optional[str] = None,
                        record_type: Optional[str] = None,
                        storage_class: Optional[str] = None,
                        source_ip_address: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate statistics based on query conditions with grouping.
        
        Args:
            group_by: List of fields to group by (supported: bucket, source_ip_address)
            start_time: Start time for record_timestamp range (ISO format)
            end_time: End time for record_timestamp range (ISO format)
            bucket: S3 bucket name
            record_type: Type of record
            storage_class: S3 storage class
            source_ip_address: Source IP address
            
        Returns:
            List of statistics grouped by specified fields
        """
        valid_group_fields = {"bucket", "source_ip_address"}
        group_fields = [field for field in group_by if field in valid_group_fields]
        
        if not group_fields:
            raise ValueError("Must specify at least one valid group_by field (bucket or source_ip_address)")
            
        where_clause = build_where_clause(
            start_time, end_time, bucket, record_type,
            storage_class, source_ip_address
        )
        
        group_by_clause = ", ".join(group_fields)
        
        query = f"""
        SELECT {group_by_clause},
               COUNT(*) as total_objects,
               SUM(size) as total_size,
               COUNT(DISTINCT record_type) as unique_record_types,
               COUNT(DISTINCT storage_class) as unique_storage_classes
        FROM {athena_config['database']}.{athena_config['table']}
        {where_clause}
        GROUP BY {group_by_clause}
        """
        
        return execute_query(query)
    

def main():
    """Entry point for the MCP server."""
    # Initialize and run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
