import smtplib

s = smtplib.SMTP('s.mailservice25.com', 587, timeout=30)
s.set_debuglevel(1)
s.ehlo()
s.starttls()
s.ehlo()
s.login('webmaster@deducetech.in', 'Welcome@2025')
s.quit()