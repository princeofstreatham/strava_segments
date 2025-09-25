variable "dbs" {
  type = map(object({
    tier      = string
    disk_size = number
    public    = bool
  }))
  default = {
    dev  = { tier = "db-f1-micro", disk_size = 10, disk_type = "PD_HDD", public = true }
    prod = { tier = "db-g1-small", disk_size = 10, disk_type = "PD_SSD", public = true }
  }
}

variable "whitelisted_ip" {
  type        = string
  description = "IP Address to access DBs from"
}

