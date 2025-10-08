# Java Installation Guide for Bldr Empire v2

## Why Java is Required
Neo4j Enterprise Edition requires Java to run. The one_click_start.bat script will check for Java and notify you if it's missing.

## Important Java Version Requirement
Neo4j Enterprise Edition 2025.08.0 requires **Java 21 or later**. Java 17 will not work.

## How to Install Java

1. **Download OpenJDK 21 (LTS)**
   - Go to https://adoptium.net/
   - Click on "Latest release" or "Latest LTS release"
   - Select Java 21
   - Choose your operating system (Windows)
   - Select "JDK" (not JRE)
   - Download the installer (usually a .msi file for Windows)

2. **Install Java**
   - Run the downloaded installer
   - Follow the installation wizard
   - Make sure to add Java to your PATH (this is usually selected by default)

3. **Verify Installation**
   - Open a new Command Prompt or PowerShell window
   - Run: `java -version`
   - You should see output similar to:
     ```
     openjdk version "21.0.4" 2024-07-16
     OpenJDK Runtime Environment (build 21.0.4+7)
     OpenJDK 64-Bit Server VM (build 21.0.4+7, mixed mode, sharing)
     ```

4. **Restart Your Computer**
   - This ensures all environment variables are properly loaded

5. **Run one_click_start.bat Again**
   - After installing Java and restarting, run the one_click_start.bat script again

## Troubleshooting

If you still get errors after installing Java:

1. **Check JAVA_HOME Environment Variable**
   - Open System Properties
   - Go to Advanced > Environment Variables
   - Check if JAVA_HOME is set to your Java installation directory
   - If not, add it:
     - Variable name: `JAVA_HOME`
     - Variable value: Path to your Java installation (e.g., `C:\Program Files\Java\jdk-21.0.4`)

2. **Check PATH Environment Variable**
   - In the same Environment Variables window
   - Find the PATH variable in System Variables
   - Make sure it includes the path to Java's bin directory (e.g., `C:\Program Files\Java\jdk-21.0.4\bin`)

3. **Restart Command Prompt/PowerShell**
   - Close all Command Prompt and PowerShell windows
   - Open new ones to load the updated environment variables