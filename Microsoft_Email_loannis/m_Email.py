import imaplib
import email
import datetime
from email.header import decode_header

# your email and password
email_user = "email"
email_pass = "password"

# create an IMAP4 class with SSL 
mail = imaplib.IMAP4_SSL("outlook.office365.com")
# authenticate
mail.login(email_user, email_pass)

# select the mailbox you want to delete in
# if you want SPAM, use "INBOX.SPAM"
mailbox = "INBOX"
mail.select(mailbox)

# get unread mail
result, data = mail.uid('search', None, '(UNSEEN)')

if result == 'OK':
    for num in data[0].split():
        result, email_data = mail.uid('fetch', num, '(BODY.PEEK[HEADER])')
        if result == 'OK':
            raw_email = email_data[0][1].decode("utf-8")
            email_message = email.message_from_string(raw_email)

            # Header Details
            date_tuple = email.utils.parsedate_tz(email_message['Date'])
            if date_tuple:
                local_date = datetime.datetime.fromtimestamp(
                    email.utils.mktime_tz(date_tuple))
                local_message_date = "%s" %(str(local_date.strftime("%a, %d %b %Y %H:%M:%S")))

            # Decoding email headers
            def decode_header(header):
                decoded, charset = email.header.decode_header(header)[0]
                if charset:
                    return decoded.decode(charset)
                else:
                    return decoded

            email_from = decode_header(email_message['From'])
            email_to = decode_header(email_message['To'])
            subject = decode_header(email_message['Subject'])

            print('From : ' + email_from + '\n')
            print('To : ' + email_to + '\n')
            print('Subject : ' + subject + '\n')
