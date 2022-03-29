packer {
  required_plugins {
    docker = {
      version = ">= 0.0.7"
      source = "github.com/hashicorp/docker"
    }
  }
}

source "docker" "alpine" {
  changes = [
    "WORKDIR /opt/trading",
    "ENTRYPOINT [\"python3\", \"-u\", \"/opt/trading/main.py\"]"
  ]
  image  = "python:3.10.2-alpine3.15"
  commit = true
}

build {
  name    = "tradebot"
  sources = ["source.docker.alpine"]

  provisioner "file" {
    source = "./5050-Long-Only/"
    destination = "/opt/trading"
  }

  provisioner "shell" {
    inline = [
        "mkdir -p /opt/trading",
        "cd /opt/trading",
        "python3 -m pip install -r /opt/trading/requirements.txt"
    ]
  }

  post-processors {

    post-processor "docker-tag" {
      repository =  "registry:5000/tradebot"
      tags = ["alpine"]
    }

    post-processor "docker-push" {}
  }
}                                                                                                                                                                  