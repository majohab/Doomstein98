terraform {
required_version = ">= 0.14.0"
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 1.47.0"
    }
  }
}

provider "openstack" {
  cloud = "openstack"
}

data "template_file" "user_data" {
  template = file("./cloud_init.yaml")
}

# Manager
resource "openstack_compute_instance_v2" "SwarmManager" {
  name            = "SwarmManager"
  image_id        = "e6da7b16-5fef-4a15-a417-db4f68c30312"
  flavor_name     = "m1.small"
  key_pair        = "cloudkey"
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
  key_pair        = "cloudkey"
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
  key_pair        = "cloudkey"
  security_groups = [openstack_networking_secgroup_v2.SwarmSec.name]
  user_data       =  data.template_file.user_data.rendered
  network {
    name = "public-belwue"
  }
}

# Install docker on each instance
resource "null_resource" "InstallDocker" {
  provisioner "local-exec"  {
    command = "ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -u lasse -i '${openstack_compute_instance_v2.SwarmManager.access_ip_v4},' --private-key ../../CloudComputing/keys/cloud_2.ppk ansible/playbook.yml"
  }
  provisioner "local-exec"  {
    command = "ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -u lasse -i '${openstack_compute_instance_v2.Worker1.access_ip_v4},' --private-key ../../CloudComputing/keys/cloud_2.ppk ansible/playbook.yml"
  }
  provisioner "local-exec"  {
    command = "ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -u lasse -i '${openstack_compute_instance_v2.Worker2.access_ip_v4},' --private-key ../../CloudComputing/keys/cloud_2.ppk ansible/playbook.yml"
  }
}
#------------------------------------------------------------------------------
# Security Group for Swarm Manager.... egress no limitation
# -----------------------------------------------------------------------------
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
#------------------------------------------------------------------------------
# Security Group for workers  .. egress no limitation
# -----------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------
#  Get an additional shared volume (beside the Ubuntu Images) to be used by all nodes
# ------------------------------------------------------------------------------
resource "openstack_blockstorage_volume_v3" "volume_1" {
  name = "mysharedVolume"
  size = 1
  multiattach = true
}
# ------------------------------------------------------------------------------
#  Attach the volume to the Swarm Manager
# ------------------------------------------------------------------------------
resource "openstack_compute_volume_attach_v2" "attach-1" {
  instance_id = "${openstack_compute_instance_v2.SwarmManager.id}"
  volume_id   = "${openstack_blockstorage_volume_v3.volume_1.id}"
  multiattach = true
}
# ------------------------------------------------------------------------------
#  Attach the volume to the Worker 1
# ------------------------------------------------------------------------------
resource "openstack_compute_volume_attach_v2" "attach-2" {
  instance_id = "${openstack_compute_instance_v2.Worker1.id}"
  volume_id   = "${openstack_blockstorage_volume_v3.volume_1.id}"
  multiattach = true
}
# ------------------------------------------------------------------------------
#  Attach the volume to the Wokrer 2
# ------------------------------------------------------------------------------
resource "openstack_compute_volume_attach_v2" "attach-3" {
  instance_id = "${openstack_compute_instance_v2.Worker2.id}"
  volume_id   = "${openstack_blockstorage_volume_v3.volume_1.id}"
  multiattach = true
}
# -----------------------------------------------------------------------------
# Format the Volume and mount it as  /mydata  (wait for the first attachement) and if done
# build the python flask image
# -----------------------------------------------------------------------------
resource "null_resource" "volumeformating" {
 connection {
   type = "ssh"
    host = openstack_compute_instance_v2.SwarmManager.access_ip_v4
    user = "juergen"
    port = 22
    private_key = file("/Users/juergenschneider/Documents/webpages/DHBW/Cloud2022/InternalStuff/BWCloud/cloud.key")
  }
  provisioner "remote-exec" {
      inline = [
      "sudo mkfs -t ext4 ${openstack_compute_volume_attach_v2.attach-1.device}",
      "sudo mkdir /mydata",
      "sudo mount ${openstack_compute_volume_attach_v2.attach-1.device} /mydata",
      "sudo chmod ugo+rwx /mydata",
    ]
 }
}
# -----------------------------------------------------------------------------
# Mount the volume to worker 1 and build Python flask
# -----------------------------------------------------------------------------
resource "null_resource" "volumemountworker1" {
  depends_on = [openstack_compute_instance_v2.Worker1,null_resource.volumeformating,null_resource.softwareconfig,null_resource.InstallDocker]
  triggers = { thisfile_hash = "${sha1(file("${path.cwd}/swarm.tf"))}" }
 connection {
   type = "ssh"
    host = openstack_compute_instance_v2.Worker1.access_ip_v4
    user = "juergen"
    port = 22
    private_key = file("/Users/juergenschneider/Documents/webpages/DHBW/Cloud2022/InternalStuff/BWCloud/cloud.key")
  }
  provisioner "remote-exec" {
      inline = [
      "sudo mkdir /mydata",
      "sudo umount ${openstack_compute_volume_attach_v2.attach-2.device} /mydata",
      "sudo mount ${openstack_compute_volume_attach_v2.attach-2.device} /mydata",
      "sudo chmod ugo+rwx /mydata",
      "cd /mydata",
      "sudo docker build -t mypython:latest --network=host --build-arg InstanceName=worker1 ."
    ]
 }
}
# -----------------------------------------------------------------------------
# Mount the volume to worker 2 and Python flask
# -----------------------------------------------------------------------------
resource "null_resource" "volumemountworker2" {
  depends_on = [openstack_compute_instance_v2.Worker2,null_resource.volumeformating,null_resource.softwareconfig,null_resource.InstallDocker]
  triggers = { thisfile_hash = "${sha1(file("${path.cwd}/swarm.tf"))}" }
 connection {
   type = "ssh"
    host = openstack_compute_instance_v2.Worker2.access_ip_v4
    user = "juergen"
    port = 22
    private_key = file("/Users/juergenschneider/Documents/webpages/DHBW/Cloud2022/InternalStuff/BWCloud/cloud.key")
  }
  provisioner "remote-exec" {
      inline = [
      "sudo mkdir /mydata",
      "sudo umount ${openstack_compute_volume_attach_v2.attach-3.device} /mydata",
      "sudo mount ${openstack_compute_volume_attach_v2.attach-3.device} /mydata",
      "sudo chmod ugo+rwx /mydata",
      "cd /mydata",
      "sudo docker build -t mypython:latest --network=host --build-arg InstanceName=worker2  ."
    ]
 }
}
# -----------------------------------------------------------------------------
# Copy the docker App yaml and all other application artifacts
# -----------------------------------------------------------------------------
resource "null_resource" "softwareconfig" {
 depends_on = [openstack_compute_instance_v2.SwarmManager,null_resource.volumeformating,null_resource.InstallDocker]
 triggers = { thisfile_hash = "${sha1(file("${path.cwd}/swarm.tf"))}" }
 connection {
   type = "ssh"
    host = openstack_compute_instance_v2.SwarmManager.access_ip_v4
    user = "juergen"
    port = 22
    private_key = file("~/Documents/webpages/DHBW/Cloud2022/InternalStuff/BWCloud/cloud.key")
  }
  provisioner "file" {
  source      = "/Users/juergenschneider/Documents/webpages/DHBW/Cloud2022/InternalStuff/BWCloud/DockerSwarm/app/"
  destination = "/mydata/"
  }
  provisioner "remote-exec" {
      inline = [
      "cd /mydata",
      "sudo docker build -t mypython:latest --network=host --build-arg InstanceName=swarmmanager  ."
    ]
 }
 }
 # -----------------------------------------------------------------------------
 # to put Docker in Swarm Node please enter the following commands
 #  Swarn Manager sudo docker swarm init --advertise-addr <192.168.xx.yy>
 #  after that a join command with a certain tokenis proposed for all workers
 #  sudo docker swarm join --token SWMTKN-1-2otb7izdwdzu67ca51wuzjcla4rlc7zox616yeff526508t83i-95hvg59ioj9xto2ryhn33pg7l 192.168.1.155:2377
 # -----------------------------------------------------------------------------
 # now we are ready to start the swarm service
 # on the manager Node on /mydata
 # sudo docker stack deploy --compose-file dockerswarm-app.yml juergenapp
 # sudo docker stack ls
 # sudo docker stack ps juergenapp  -> Status anschauen
 # sudo docker stack services juergenapp
 # sudo docker stack rm juergenapp
 #
