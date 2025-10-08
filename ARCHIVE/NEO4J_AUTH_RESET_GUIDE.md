# Neo4j Authentication Reset Guide

## Issue
You're experiencing authentication failures with Neo4j due to "AuthenticationRateLimit" errors. This happens when there have been too many failed authentication attempts in a row, causing Neo4j to temporarily block further attempts.

## Solution

### Step 1: Stop Neo4j Completely
1. Close Neo4j Desktop application completely
2. Wait 1-2 minutes for all processes to terminate
3. Verify no Java processes are running:
   ```
   tasklist | findstr java
   ```
   If any remain, kill them with:
   ```
   taskkill /F /PID <process_id>
   ```

### Step 2: Reset Neo4j Authentication
1. Open Neo4j Desktop
2. Find your database instance (Bldr2)
3. Click on the "Manage" button for your instance
4. Go to the "Settings" tab
5. Find the line that says `dbms.security.auth_enabled=true`
6. Change it to `dbms.security.auth_enabled=false`
7. Click "Apply" and restart the database instance

### Step 3: Test Connection Without Authentication
1. Run the test script to verify connection works without authentication:
   ```
   python test_neo4j_connection_simple.py
   ```

### Step 4: Reset Password (Optional but Recommended)
1. With authentication disabled, connect to Neo4j Browser at http://localhost:7474
2. You should be able to access without a password
3. In the Neo4j Browser command line, run:
   ```
   ALTER USER neo4j SET PASSWORD 'neopassword'
   ```
4. Then re-enable authentication by changing `dbms.security.auth_enabled=false` back to `dbms.security.auth_enabled=true`
5. Restart the database instance

### Step 5: Update Your .env File
Make sure your [c:\Bldr\.env](file:///C:/Bldr/.env) file contains the correct credentials:
```
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neopassword
REDIS_URL=redis://localhost:6379
ALLOW_TEST_TOKEN=true
```

### Step 6: Test Connection Again
1. Run the test script to verify connection works with authentication:
   ```
   python test_neo4j_connection_simple.py
   ```

## Alternative Quick Fix (If Above Doesn't Work)

If you continue to have issues, try these steps:

1. Completely stop Neo4j Desktop
2. Navigate to your Neo4j database folder (usually in `C:\Users\[username]\Documents\Neo4j\`)
3. Find your database instance folder
4. Delete the `data/dbms/auth` file (this will reset authentication)
5. Restart Neo4j Desktop and your database instance
6. The default password should now be `neo4j` again

## Prevention

To avoid this issue in the future:
1. Make sure your credentials in the .env file match exactly what's configured in Neo4j
2. Avoid rapid repeated connection attempts
3. If you change passwords, update your .env file immediately