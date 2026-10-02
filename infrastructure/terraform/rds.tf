resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_db_instance" "postgres" {
  identifier     = "${var.project_name}-db"
  engine         = "postgres"
  engine_version = "17"

  # Smallest Graviton class, eligible for the RDS free tier -- not Aurora,
  # which bills for storage I/O separately and costs more at this scale.
  instance_class    = "db.t4g.micro"
  allocated_storage = 20
  storage_type      = "gp3"

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  publicly_accessible     = false
  multi_az                = false # single-AZ to minimize cost -- not production-grade HA
  backup_retention_period = 1
  skip_final_snapshot     = true # acceptable for a demo project; would be false in production
}
