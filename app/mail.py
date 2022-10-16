from flask import render_template, current_app
from flask_mail import Mail, Message
from configure import conf

mail = Mail()


def send_msg(title: str, to, template, **kwargs):
    """ 邮件发送 """
    sender = f"HTalk Admin <{conf['MAIL_SENDER']}>"
    message = Message(conf['MAIL_PREFIX'] + title, sender=sender, recipients=[to])
    message.body = render_template("email-msg/" + template + ".txt", **kwargs)
    message.html = render_template("email-msg/" + template + ".html", **kwargs)
    mail.send(message)
    current_app.logger.info(f"Send email to {to} sender: {sender} msg: {template} kwargs: {kwargs}")
