output "certificate_arn" {
   description = "Certificate value for ALB"
   value = aws_acm_certificate.cert.arn
}   
