#!/usr/bin/env python

from subprocess import check_output

from rmapp.lib.common import *


class Authenticator(object):

    def generate_public_certification(self, tmp_folder):

        variables = {"tmp_folder": tmp_folder}
        output_file = "%s/generate_certificate" % (tmp_folder)
        generate_template("authenticator/generate_certificate.jinja2", variables)
        generate_template_file("authenticator/generate_certificate.jinja2", output_file, variables)
        out = check_output(["bash", "%s" % (output_file)])

        return out

    def decrypt_password(self, tmp_folder):

        variables = {"tmp_folder": tmp_folder}
        generate_template("authenticator/decrypt_password.jinja2", variables)
        output_file = "%s/decrypt_password" % (tmp_folder)
        generate_template_file("authenticator/decrypt_password.jinja2", output_file, variables)
        out = check_output(["bash", "%s" % (output_file)]).strip()

        return out


if __name__ == "__main__":

    authenticator = Authenticator()
    authenticator.generate_public_certification("tmp/3b225f4d-d468-44d1-bc44-f6b54ab8e0a8")
