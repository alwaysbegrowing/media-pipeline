
class EmailTemplate:
    def __init__(self, subject: str, html) -> None:
        self.template = {
            'Subject': {
                'Data': subject
            },
            'Body': {
                'Html': {
                    'Data': html
                }
            }
        }


class HtmlTemplate():
    header = f'''
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html>
    <meta http-equiv="Content-Type" content="text/html charset=UTF-8" />
    <head>
    </head>
    '''

    footer = f'''<br>
    <a href="https://discord.gg/dhT6UUgf9v"> Join the Pillar Discord! </a>
    <br>
    <br>
    Thanks for using Pillar! <br>
    See you soon, <br>
    The Pillar Team
    </body>
    </html>
    '''

    def __init__(self, subject: str, html: str) -> None:
        self.subject = subject
        self._html = html

    @property
    def message(self):
        modified_html = self.header + self._html + self.footer
        return EmailTemplate(self.subject, modified_html).template


class S3Success(HtmlTemplate):
    subject = 'Your Pillar Export is Ready! (link inside)'

    def __init__(self, display_name: str, file: str) -> None:
        html = f'''
            <body>
            {display_name}, <br>
            Here is your Pillar compilation: <br>
            {file}
            '''
        super().__init__(self.subject, html)


class FailureMessage(HtmlTemplate):
    subject = 'Your Pillar compilation failed'

    def __init__(self, display_name: str, error_name: str) -> None:
        html = f'''
            <body>
            {display_name}, <br>
            There was an error creating the compilation :( <br>
            Please reply to this email or ping us on the Discord server and we will be happy to fix it!<br>
            '''
        super().__init__(self.subject, html)


class YoutubeSuccess(HtmlTemplate):
    subject = 'Your Pillar Video is Ready! (links inside)'

    def __init__(self, display_name: str, file: str, s3_file: str) -> None:
        html = f'''
        <body>
        {display_name}, <br>
        Your video has been uploaded to YouTube! <br>
        Youtube URL: {file} <br>
        Raw File: {s3_file}
        '''
        super().__init__(self.subject, html)
