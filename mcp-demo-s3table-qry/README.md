# AWS S3 Table Query MCP Server

This MCP Server provides an interface to query AWS Athena for S3 table analytics data. It supports querying and analyzing S3 object metadata including bucket statistics, record types, storage classes, and more.

## Features

- Query records based on various conditions:
  - Time range (record_timestamp)
  - Bucket
  - Record type
  - Storage class
  - Source IP address
  - And more...
- Generate statistics grouped by bucket and source IP address
- Configurable query parameters for database, table, and catalog

## Configuration

The server requires the following environment variables to be set:

```bash
# Required variables
ATHENA_DATABASE=your_database
ATHENA_TABLE=your_table
ATHENA_OUTPUT_LOCATION=s3://your-bucket/athena-results/

# Optional variables
ATHENA_CATALOG=your_catalog  # Optional
AWS_REGION=your-region       # Defaults to us-east-1
```

Make sure to set these environment variables before starting the server. Missing required variables will cause the server to fail at startup.

## Tools

### 1. query_record

Query S3 object records based on various conditions:

- record_timestamp range
- bucket
- record_type
- storage_class
- source_ip_address

### 2. query_statistics

Generate statistics based on the same query conditions as query_record, with additional grouping support by:

- bucket
- source_ip_address

## Configure MCP Client
Using the example of the Claude Code as an MCP Client, as follows:
```bash
npm install -g @anthropic-ai/claude-code
export CLAUDE_CODE_USE_BEDROCK=1
export ANTHROPIC_MODEL='us.anthropic.claude-3-7-sonnet-20250219-v1:0'
claude
```

Add your MCP Server
```json
claude mcp add-json s3table-mcp-server '{
  "type": "stdio",
  "command": "uv",
  "args": [
    "--directory",
    "/Users/xxx/mcp-server-python/aws_s3table_query",
    "run",
    "server.py"
  ],
  "env": {
    "ATHENA_CATALOG": "s3tablescatalog",
    "ATHENA_DATABASE": "aws_s3_metadata",
    "ATHENA_TABLE": "s3metadata_imagebucket_us_east_1",
    "ATHENA_OUTPUT_LOCATION": "s3://aws-athena-xxx-us-east-1/"
  }
}'
```
User needs to replace the following parts:

1. s3table-mcp-server: The name of your MCP server configuration, which can be customized according to your application scenario

2. /Users/xxx/mcp-server-python/aws_s3table_query: The directory path to your local MCP server code

3. Environment variables:

ATHENA_CATALOG: The name of your Athena catalog
ATHENA_DATABASE: The name of your Athena database
ATHENA_TABLE: The name of the table you want to query
ATHENA_OUTPUT_LOCATION: The S3 output location for Athena query results, ensure it ends with a slash
Verify if it was added successfully:
```bash
claude mcp list
```