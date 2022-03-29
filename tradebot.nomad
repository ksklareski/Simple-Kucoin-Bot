variables {
    min_healthy_sec = 10
    image_url = "registry:5000/tradebot:alpine"
    container_cpu = 200
    container_mem = 50
    API_KEY = ""
    API_SECRET = ""
    API_PASSPHRASE = ""
    API_URL = ""
    PAIR = ""
    MAX_LEVERAGE = ""
    TAKE_PROFIT_PERCENT = ""
    STOP_LOSS_PERCENT = ""
}

job "tradebot" {
  datacenters = ["home"]
  type = "service"

  meta {
    // This essentially forces an update every time the job is run
    uuid = uuidv4()
  }

  update {
    max_parallel = 1
    min_healthy_time = var.min_healthy_sec
    healthy_deadline = "3m"
    progress_deadline = "10m"
    auto_revert = false
    canary = 0
  }
  migrate {
    max_parallel = 1
    health_check = "checks"
    min_healthy_time = var.min_healthy_sec
    healthy_deadline = "5m"
  }

  group "tradebot-group" {
    task "tradebot" {
      driver = "docker"

      config {
        image = var.image_url
      }

      resources {
        cpu = var.container_cpu
        memory = var.container_mem
      }

      env {
        KUCOIN_API_KEY = var.API_KEY
        KUCOIN_API_SECRET = var.API_SECRET
        KUCOIN_API_PASSPHRASE = var.API_PASSPHRASE
        KUCOIN_API_URL = var.API_URL
        KUCOIN_PAIR = var.PAIR
        KUCOIN_MAX_LEVERAGE = var.MAX_LEVERAGE
        KUCOIN_TAKE_PROFIT_PERCENT = var.TAKE_PROFIT_PERCENT
        KUCOIN_STOP_LOSS_PERCENT = var.STOP_LOSS_PERCENT
      }
    }
  }
}