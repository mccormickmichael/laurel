
class ConsulSoftware(object):  # this name sucks.

    VERSION = '0.6.4'

    URL_PREFIX = 'https://releases.hashicorp.com/consul/{0}/'.format(VERSION)

    LINUX_NAME = 'consul_{0}_linux_amd64.zip'.format(VERSION)
    WINDOWS_NAME = 'consul_{0}_windows_amd64.zip'.format(VERSION)
    WEB_NAME = 'consul_{0}_web_ui.zip'.format(VERSION)

    S3_KEY_PREFIX = 'software/consul/{0}/'.format(VERSION)

    @classmethod
    def components(cls):
        return [
            {
                'name': cls.LINUX_NAME,
                'url': cls.linux_url(),
                's3_key': cls.linux_s3_key()
            },
            {
                'name': cls.WINDOWS_NAME,
                'url': cls.windows_url(),
                's3_key': cls.windows_s3_key()
            },
            {
                'name': cls.WEB_NAME,
                'url': cls.ui_url(),
                's3_key': cls.ui_s3_key()
            }
        ]

    @classmethod
    def linux_url(cls):
        return cls.URL_PREFIX + cls.LINUX_NAME

    @classmethod
    def windows_url(cls):
        return cls.URL_PREFIX + cls.WINDOWS_NAME

    @classmethod
    def ui_url(cls):
        return cls.URL_PREFIX + cls.WEB_NAME

    @classmethod
    def linux_s3_key(cls):
        return cls.S3_KEY_PREFIX + cls.LINUX_NAME

    @classmethod
    def windows_s3_key(cls):
        return cls.S3_KEY_PREFIX + cls.LINUX_NAME

    @classmethod
    def ui_s3_key(cls):
        return cls.S3_KEY_PREFIX + cls.LINUX_NAME
