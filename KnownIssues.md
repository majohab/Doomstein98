### Bug: Provider produced inconsistent final plan
- Delete known hosts (or just try again lol)

### file provisioner error: Upload failed: Process exited with status 1
- Option 1: Delete known hosts:
    - sudo rm /home/studium/.ssh/known_hosts
- Option 2: Redo everything: Delete Lock File, run terraform init

### remote-exec provisioner error: error executing "/tmp/terraform_289808385.sh"
-