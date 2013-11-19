# Turning this on will attempt to connect to the server anonymously without using the domain credentials
ANONYMOUS = False

# Resolve SID's from NTFS perm dumps - must be joined to domain
ENABLE_SID_RESOLUTION = True

#Where the folders will be mounted for permissions gathering
MOUNT_LOCATION = "/mnt/scan/"

# Domain credentials for scanning
USERNAME = ''
PASSWORD = ''
DOMAIN = ""

# Setting these up allows us to resolve the SID's pulled by the GET NTFS ACL potion of the tool.
# User/pass can be different to allow different priviledges on lookup acct. vs scanning account
LDAP_USERNAME = ""
LDAP_PASSWORD = ""
DOMAIN_CONTROLLER = ''
SEARCH_BASE = ""

# What are we scanning
TARGET_LIST = "targets.txt"

# OBSOLETE
# This will output an "ls"-style output for easy grepping/awking
# OUTPUT_FILE = "test.txt"

# Limit the number of connections -- we make one SMB scanner thread per system in the targets file
MAX_THREADS = 16

# Limit on the number of mounts -- Linux can only handel 255 mounts at a time
MOUNT_LIMIT = 100

#Database Settings
DB_NAME = "smb_scan"
DB_USR = "postgres"
DB_PASS = "postgres"
DB_HOST = "127.0.0.1"
DB_PORT = 5432
