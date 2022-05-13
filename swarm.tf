# Configure terraform version
terraform {
required_version = ">= 0.14.0"
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 1.47.0"
    }
  }
}
# Configure stack provider
provider "openstack" {
  cloud = "openstack"
}

data "template_file" "user_data" {
  template = file("./cloud_init.yaml")
}

# Create Instances
# Manager
resource "openstack_compute_instance_v2" "SwarmManager" {
  name            = "SwarmManager"
  image_id        = "e6da7b16-5fef-4a15-a417-db4f68c30312"
  flavor_name     = "m1.small"
  key_pair        = "Windows"
  security_groups = [openstack_networking_secgroup_v2.SwarmSec.name]
  user_data       =  data.template_file.user_data.rendered
  network {
    name = "public-belwue"
  }
}

# Worker 1
resource "openstack_compute_instance_v2" "Worker1" {
  name            = "Worker1"
  image_id        = "e6da7b16-5fef-4a15-a417-db4f68c30312"
  flavor_name     = "m1.small"
  key_pair        = "Windows"
  security_groups = [openstack_networking_secgroup_v2.SwarmSec.name]
  user_data       =  data.template_file.user_data.rendered
  network {
    name = "public-belwue"
  }
}

# Worker 2
resource "openstack_compute_instance_v2" "Worker2" {
  name            = "Worker2"
  image_id        = "e6da7b16-5fef-4a15-a417-db4f68c30312"
  flavor_name     = "m1.small"
  key_pair        = "Windows"
  security_groups = [openstack_networking_secgroup_v2.SwarmSec.name]
  user_data       =  data.template_file.user_data.rendered
  network {
    name = "public-belwue"
  }
}

# -----------------------------------------------------------------------------
# Install docker on each instance via Ansible
# -----------------------------------------------------------------------------
resource "null_resource" "InstallDocker" {
  provisioner "local-exec"  {
    command = "ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -u debian -i '${openstack_compute_instance_v2.SwarmManager.access_ip_v4},' --private-key /home/.ssh/Windows.pem ansible/playbook.yml"
  }
  provisioner "local-exec"  {
    command = "ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -u debian -i '${openstack_compute_instance_v2.Worker1.access_ip_v4},' --private-key /home/.ssh/Windows.pem ansible/playbook.yml"
  }
  provisioner "local-exec"  {
    command = "ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -u debian -i '${openstack_compute_instance_v2.Worker2.access_ip_v4},' --private-key /home/.ssh/Windows.pem ansible/playbook.yml"
  }
}

# -----------------------------------------------------------------------------
# Security Groups
# -----------------------------------------------------------------------------

# Security Group for Swarm Manager.... egress no limitation

resource "openstack_networking_secgroup_v2" "SwarmSec" {
    name = "SwarmSec"
    description = "Terraform generated Security, to enable Docker Swarm Manager"
}
resource "openstack_networking_secgroup_rule_v2" "workerrule1" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.SwarmSec.id
}
resource "openstack_networking_secgroup_rule_v2" "workerrule1a" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "icmp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.SwarmSec.id
}
resource "openstack_networking_secgroup_rule_v2" "workerrule1b" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "udp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.SwarmSec.id
}

# Security Group for workers  .. egress no limitation

resource "openstack_networking_secgroup_v2" "SwarmWorkerSec" {
    name = "SwarmWorkerSec"
    description = "Terraform generated Security, to enable Docker Swarm Worker"
}
resource "openstack_networking_secgroup_rule_v2" "workerrule2" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  remote_ip_prefix  = "192.168.0.0/16"
  security_group_id = openstack_networking_secgroup_v2.SwarmWorkerSec.id
}
resource "openstack_networking_secgroup_rule_v2" "workerrule2a" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "icmp"
  remote_ip_prefix  = "192.168.0.0/16"
  security_group_id = openstack_networking_secgroup_v2.SwarmWorkerSec.id
}
resource "openstack_networking_secgroup_rule_v2" "workerrule2b" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "udp"
  remote_ip_prefix  = "192.168.0.0/16"
  security_group_id = openstack_networking_secgroup_v2.SwarmWorkerSec.id
}

# -----------------------------------------------------------------------------
# Create, attach and mount a Shared Volume
# -----------------------------------------------------------------------------

# Get an additional shared volume (beside the Ubuntu Images) to be used by all nodes
resource "openstack_blockstorage_volume_v3" "volume_1" {
  name = "sharedvolume"
  size = 10
  multiattach = true
}

#  Attach the volume to the Swarm Manager
resource "openstack_compute_volume_attach_v2" "attach_manager" {
  instance_id = "${openstack_compute_instance_v2.SwarmManager.id}"
  volume_id   = "${openstack_blockstorage_volume_v3.volume_1.id}"
  multiattach = true
}

#  Attach the volume to the Worker 1
resource "openstack_compute_volume_attach_v2" "attach_worker1" {
  instance_id = "${openstack_compute_instance_v2.Worker1.id}"
  volume_id   = "${openstack_blockstorage_volume_v3.volume_1.id}"
  multiattach = true
}

#  Attach the volume to the Worker 2
resource "openstack_compute_volume_attach_v2" "attach_worker2" {
  instance_id = "${openstack_compute_instance_v2.Worker2.id}"
  volume_id   = "${openstack_blockstorage_volume_v3.volume_1.id}"
  multiattach = true
}

# Format the Volume and mount it as /home/debian/data on SwarmManager (wait for the first attachement) 
resource "null_resource" "volume_formattingAndMounting" {
 depends_on = [openstack_compute_volume_attach_v2.attach_manager, openstack_compute_instance_v2.SwarmManager, null_resource.InstallDocker]
 connection {
   type = "ssh"
    host = openstack_compute_instance_v2.SwarmManager.access_ip_v4
    user = "debian"
    port = 22
    private_key = file("/home/.ssh/Windows.pem")
  }
  provisioner "remote-exec" {
    inline = [
      "sudo mkfs -t ext4 ${openstack_compute_volume_attach_v2.attach_manager.device}",
      "sudo mkdir /home/debian/data",
      "sudo mount ${openstack_compute_volume_attach_v2.attach_manager.device} /home/debian/data",
      "sudo chmod 777 /home/debian/data -R",
    ]
  }
}

# Note that mounting a shared volume doesn't seem to work here. (Seems like a bug.)
# Therefore, in the following section, we only create the directories for the volume and mount it later manually.

# Create Shared Volume Directory on Worker 1
resource "null_resource" "volume_mount_worker1" {
  depends_on = [openstack_compute_instance_v2.Worker1, openstack_compute_volume_attach_v2.attach_worker1, null_resource.volume_formattingAndMounting, null_resource.InstallDocker]
  triggers = { thisfile_hash = "${sha1(file("${path.cwd}/swarm.tf"))}" }
 connection {
   type = "ssh"
    host = openstack_compute_instance_v2.Worker1.access_ip_v4
    user = "debian"
    port = 22
    private_key = file("/home/.ssh/Windows.pem")
  }
  provisioner "remote-exec" {
    inline = [
      "sudo mkdir /home/debian/data",
      "sudo mount ${openstack_compute_volume_attach_v2.attach_manager.device} /home/debian/data",
    ]
  }
}

# Create Shared Volume Directory on Worker 2
resource "null_resource" "volume_mount_worker2" {
  depends_on = [openstack_compute_instance_v2.Worker1, openstack_compute_volume_attach_v2.attach_worker2, null_resource.volume_formattingAndMounting, null_resource.InstallDocker]
  triggers = { thisfile_hash = "${sha1(file("${path.cwd}/swarm.tf"))}" }
 connection {
   type = "ssh"
    host = openstack_compute_instance_v2.Worker2.access_ip_v4
    user = "debian"
    port = 22
    private_key = file("/home/.ssh/Windows.pem")
  }
  provisioner "remote-exec" {
    inline = [
      "sudo mkdir /home/debian/data",
      "sudo mount ${openstack_compute_volume_attach_v2.attach_manager.device} /home/debian/data",
    ]
  }
}

# -----------------------------------------------------------------------------
# Copy Doomstein98 data to volume and build images
# -----------------------------------------------------------------------------

# Copy app and build images on SwarmManager 
resource "null_resource" "swarmManager_copyAndBuildApp" {
 depends_on = [openstack_compute_instance_v2.Worker1, null_resource.InstallDocker, openstack_compute_volume_attach_v2.attach_worker2, null_resource.volume_formattingAndMounting,
              null_resource.volume_mount_worker1, null_resource.volume_mount_worker2]
 triggers = { thisfile_hash = "${sha1(file("${path.cwd}/swarm.tf"))}" }
 connection {
   type = "ssh"
    host = openstack_compute_instance_v2.SwarmManager.access_ip_v4
    user = "debian"
    port = 22
    private_key = file("/home/.ssh/Windows.pem")
  }
  provisioner "file" {
  source      = "/mnt/f/Webeng/Doomstein98"
  destination = "/home/debian/data"
  }
  provisioner "remote-exec" {
    inline = [
      "cd /home/debian/data",
      "mkdir static_data",
      "mkdir ssl_cert",
      "cd /home/debian/",
      "sudo chmod 777 data/ -R", # Not a good idea but it works @juergen
      "cd /home/debian/data/Doomstein98/",
      "sudo docker build -t app --network=host .",
      "cd /home/debian/data/Doomstein98/proxy/",
      "sudo docker build -t proxy --network=host ."
    ]
  }
}

# Build images on worker 1
resource "null_resource" "worker1_buildApp" {
 depends_on = [openstack_compute_instance_v2.Worker1, null_resource.InstallDocker, openstack_compute_volume_attach_v2.attach_worker2, null_resource.volume_formattingAndMounting,
              null_resource.volume_mount_worker1, null_resource.volume_mount_worker2,
              null_resource.swarmManager_copyAndBuildApp]
 triggers = { thisfile_hash = "${sha1(file("${path.cwd}/swarm.tf"))}" }
 connection {
   type = "ssh"
    host = openstack_compute_instance_v2.Worker1.access_ip_v4
    user = "debian"
    port = 22
    private_key = file("/home/.ssh/Windows.pem")
  }
  provisioner "remote-exec" {
    inline = [
      "cd /home/debian/",
      "sudo chmod 777 data/ -R", # Not a good idea but it works @juergen
      "cd /home/debian/data/Doomstein98/",
      "sudo docker build -t app --network=host .",
      "cd /home/debian/data/Doomstein98/proxy/",
      "sudo docker build -t proxy --network=host ."
    ]
  }
}

# Build images on worker 2
resource "null_resource" "worker2_buildApp" {
 depends_on = [openstack_compute_instance_v2.Worker1, null_resource.InstallDocker, openstack_compute_volume_attach_v2.attach_worker2, null_resource.volume_formattingAndMounting,
              null_resource.volume_mount_worker1, null_resource.volume_mount_worker2,
              null_resource.swarmManager_copyAndBuildApp, null_resource.worker1_buildApp]
 triggers = { thisfile_hash = "${sha1(file("${path.cwd}/swarm.tf"))}" }
 connection {
   type = "ssh"
    host = openstack_compute_instance_v2.Worker2.access_ip_v4
    user = "debian"
    port = 22
    private_key = file("/home/.ssh/Windows.pem")
  }
  provisioner "remote-exec" {
      inline = [
      "cd /home/debian/",
      "sudo chmod 777 data/ -R", # Not a good idea but it works @juergen
      "cd /home/debian/data/Doomstein98/",
      "sudo docker build -t app --network=host .",
      "cd /home/debian/data/Doomstein98/proxy/",
      "sudo docker build -t proxy --network=host ."
    ]
 }
}

# -----------------------------------------------------------------------------
#
# To put Docker in Swarm Node please enter the following commands
#
# Swarn Manager:
#   sudo docker swarm init --advertise-addr <192.168.xx.yy>
# Workers (command must be replaced with the output of the last command):
#   sudo docker swarm join --token SWMTKN-1-4ubfn5gb4ozje1oexm7tn8y3qwp5svhtal2y0wszfgq45ravqf-d5mpsf7wsdajra9me43yyycvq 193.196.53.136:2377
#
# -----------------------------------------------------------------------------
#
# Now we are ready to start the swarm service
# On the manager Node:
#   cd data/Doomstein98/
# (Maybe need to update .env-file: Remove whitespaces)
#   sudo docker stack deploy --compose-file docker-compose-deploy.yml doomstein98
#   sudo docker stack ls
#   sudo docker stack ps doomstein98  -> Status anschauen
#   sudo docker stack services doomstein98
#   sudo docker stack rm doomstein98
#
# Logs of stack:
#   sudo docker service logs doomstein98_redis
# -----------------------------------------------------------------------------