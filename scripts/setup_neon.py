#!/usr/bin/env python3
"""
Neon Database Setup Script
Creates project, database, and initializes schema using Neon CLI
"""
import subprocess
import sys
import json
import os


def run_command(command, capture=True):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=capture,
            text=True
        )
        if result.returncode != 0 and capture:
            print(f"Error: {result.stderr}")
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_neon_cli():
    """Check if Neon CLI is installed"""
    success, _, _ = run_command("neonctl --version")
    return success


def install_neon_cli():
    """Install Neon CLI via npm"""
    print("Installing Neon CLI...")
    success, _, _ = run_command("npm install -g neonctl", capture=False)
    return success


def authenticate_neon():
    """Authenticate with Neon"""
    print("\nAuthenticating with Neon...")
    print("This will open a browser window for authentication.")
    input("Press Enter to continue...")
    success, _, _ = run_command("neonctl auth", capture=False)
    return success


def create_project(project_name):
    """Create a new Neon project"""
    print(f"\nCreating Neon project: {project_name}")
    success, stdout, _ = run_command(f'neonctl projects create --name "{project_name}" --output json')

    if success and stdout:
        try:
            project = json.loads(stdout)
            return project
        except json.JSONDecodeError:
            pass
    return None


def get_connection_string(project_id):
    """Get connection string for a project"""
    success, stdout, _ = run_command(f'neonctl connection-string {project_id}')
    if success:
        return stdout.strip()
    return None


def list_projects():
    """List all Neon projects"""
    success, stdout, _ = run_command('neonctl projects list --output json')
    if success and stdout:
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            pass
    return []


def init_database(connection_string, schema_file):
    """Initialize database with schema"""
    print(f"\nInitializing database with schema: {schema_file}")

    # Check if psql is available
    success, _, _ = run_command("psql --version")
    if not success:
        print("Warning: psql not found. Please run the schema manually:")
        print(f"  psql \"{connection_string}\" -f {schema_file}")
        return False

    success, _, stderr = run_command(f'psql "{connection_string}" -f "{schema_file}"')
    if not success:
        print(f"Error initializing database: {stderr}")
    return success


def main():
    print("=" * 60)
    print("Neon Database Setup for Automotive Repair Management System")
    print("=" * 60)

    # Check for Neon CLI
    if not check_neon_cli():
        print("\nNeon CLI not found.")
        install = input("Would you like to install it? (y/n): ").lower()
        if install == 'y':
            if not install_neon_cli():
                print("Failed to install Neon CLI. Please install manually:")
                print("  npm install -g neonctl")
                sys.exit(1)
        else:
            print("\nPlease install Neon CLI manually:")
            print("  npm install -g neonctl")
            sys.exit(1)

    # Authenticate
    print("\nChecking Neon authentication...")
    projects = list_projects()
    if not projects:
        if not authenticate_neon():
            print("Authentication failed. Please try again.")
            sys.exit(1)

    # Create or select project
    print("\nExisting projects:")
    projects = list_projects()
    if projects:
        for i, proj in enumerate(projects):
            print(f"  {i + 1}. {proj.get('name', 'Unknown')} (ID: {proj.get('id', 'Unknown')})")

    print("\nOptions:")
    print("  1. Create new project")
    print("  2. Use existing project")

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == '1':
        project_name = input("Enter project name [automotive-repair]: ").strip()
        if not project_name:
            project_name = "automotive-repair"

        project = create_project(project_name)
        if not project:
            print("Failed to create project.")
            sys.exit(1)

        project_id = project.get('id')
        print(f"Project created: {project_name} (ID: {project_id})")

    elif choice == '2':
        if not projects:
            print("No existing projects found. Creating new one.")
            project_name = "automotive-repair"
            project = create_project(project_name)
            project_id = project.get('id') if project else None
        else:
            proj_num = input("Enter project number: ").strip()
            try:
                idx = int(proj_num) - 1
                project_id = projects[idx].get('id')
            except (ValueError, IndexError):
                print("Invalid selection.")
                sys.exit(1)
    else:
        print("Invalid choice.")
        sys.exit(1)

    # Get connection string
    print("\nRetrieving connection string...")
    connection_string = get_connection_string(project_id)

    if connection_string:
        print("\n" + "=" * 60)
        print("CONNECTION STRING (save this to .env):")
        print("=" * 60)
        print(f"\nDATABASE_URL={connection_string}")
        print("\n" + "=" * 60)

        # Initialize database
        schema_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'database', 'schema.sql'
        )

        if os.path.exists(schema_file):
            init_db = input("\nInitialize database with schema? (y/n): ").lower()
            if init_db == 'y':
                if init_database(connection_string, schema_file):
                    print("Database initialized successfully!")
                else:
                    print("Please initialize the database manually.")
        else:
            print(f"\nSchema file not found: {schema_file}")
            print("Please run the schema manually after setup.")

        # Save to .env
        save_env = input("\nSave to .env file? (y/n): ").lower()
        if save_env == 'y':
            env_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                '.env'
            )

            # Read existing .env
            existing = {}
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            existing[key] = value

            # Update DATABASE_URL
            existing['DATABASE_URL'] = connection_string

            # Write back
            with open(env_file, 'w') as f:
                for key, value in existing.items():
                    f.write(f"{key}={value}\n")

            print(f"Saved to {env_file}")

    else:
        print("Failed to get connection string.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Copy the DATABASE_URL to your Heroku config vars")
    print("2. Set up Stack Auth at https://stack-auth.com")
    print("3. Configure STACK_AUTH_PROJECT_ID in environment")
    print("4. Deploy to Heroku with: git push heroku main")


if __name__ == "__main__":
    main()
