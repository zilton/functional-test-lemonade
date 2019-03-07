import smtplib
import datetime
from string import Template
from email.mime.multipart import MIMEMultipart

address = ''
password = ''
contacts = ''
message = ''


def get_contacts(filename):
    """
    Return two lists names, emails containing names and email addresses
    read from a file specified by filename.
    """

    names = []
    emails = []
    with open(filename, mode='r') as contacts_file:
        for a_contact in contacts_file:
            contact = a_contact.split()
            names.append(contact[0])
            emails.append(contact[1])
    return names, emails


def read_template(filename):
    """
    Returns a Template object comprising the contents of the 
    file specified by filename.
    """

    with open(filename, 'r') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)


def main(message_status_report, subject):
    global contacts, message

    names, emails = get_contacts(contacts) # read contacts
    message_template = read_template(message)

    # set up the SMTP server
    server = smtplib.SMTP(host='smtp.gmail.com', port=587)
    server.starttls()
    server.login(address, password)

    # For each contact, send the email:
    for name, email in zip(names, emails):
        msg = MIMEMultipart()       # create a message

        # add in the actual person name to the message template
        today = datetime.date.today().strftime('%d/%b/%Y')
        message = message_template.substitute(PERSON_NAME=name.title(),
                                              STATUS_REPORT=message_status_report,
                                              DATE=today)

        email_text = '''Subject:%s\n
        %s
        ''' % (subject, message)

        # send the message via the server set up earlier.
        server.sendmail(from_addr=address, to_addrs=email, msg=email_text)
        del msg

    server.quit()
