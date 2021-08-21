
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
    <br>
    <br>
    Thanks for using Pillar! <br>
    See you soon, <br>
    The Pillar Team
    </body>
    </html>
    '''

    def __init__(self, html: str, subject: str) -> None:
        self._html = html
        self.subject = subject

    @property
    def message(self):
        modified_html = self.header + self._html + self.footer
        return EmailTemplate(self.subject, modified_html).template


class S3Success(HtmlTemplate):
    def __init__(self, subject, display_name: str, file: str) -> None:
        html = f'''
        <body>
        {display_name}, <br>
        Here is your Pillar compilation: <br>
        {file}
        '''
        super().__init__(subject, html)


class FailureMessage(HtmlTemplate):
    def __init__(self, subject, display_name: str, file: str) -> None:
        html = f'''
        <body>
        {display_name}, <br>
        There was an error creating the compilation :( <br>
        Please reply to this email and we will be happy to fix it!<br>
        '''
        super().__init__(subject, html)


class YoutubeSuccess(HtmlTemplate):
    def __init__(self, subject, display_name: str, file: str) -> None:
        html = f'''
        <body>
        {display_name}, <br>
        Your video has been uploaded to YouTube! <br>
        View is here: {file}        
        '''
        super().__init__(subject, html)


if __name__ == '__main__':
    x = S3Success('test', 'wow')
    y = HtmlTemplate("wtf")
    print(x.html)
