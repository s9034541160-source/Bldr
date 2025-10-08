# Reset Neo4j Authentication

If you're getting authentication errors like:
```
{code: Neo.ClientError.Security.Unauthorized} {message: The client is unauthorized due to authentication failure.}
```
or
```
{code: Neo.ClientError.Security.AuthenticationRateLimit} {message: The client has provided incorrect authentication details too many times in a row.}
```

Follow these steps to reset the authentication:

## Step 1: Stop Neo4j Completely

1. Close Neo4j Desktop application
2. Wait 1-2 minutes for all processes to terminate

## Step 2: Restart Neo4j

1. Open Neo4j Desktop application
2. Start your database instance

## Step 3: Verify Credentials

Make sure your database is using the correct credentials:
- **Username**: `neo4j`
- **Password**: `neopassword`

If you need to change the password:

1. In Neo4j Desktop, click on your database instance
2. Click "Open"
3. Go to the "Administration" tab
4. Click "Reset Password"
5. Set the new password to `neopassword`

## Step 4: Test Connection

Run the verification script:
```bash
python verify_neo4j_connection.py
```

## Step 5: Start Bldr Empire

After confirming the connection works, start the Bldr Empire system:
```bash
start_bldr.bat
```

## If Problems Persist

If you continue to have authentication issues:

1. Check your `.env` file to ensure it contains:
   ```
   NEO4J_URI=neo4j://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=neopassword
   ```

2. Try creating a new database instance in Neo4j Desktop with the correct credentials

3. Make sure no other applications are using the Neo4j database