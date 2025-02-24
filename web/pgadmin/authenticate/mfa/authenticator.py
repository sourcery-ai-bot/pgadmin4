##############################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2022, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##############################################################################
"""Multi-factor Authentication implementation for Time-based One-Time Password
(TOTP) applications"""

import base64
from io import BytesIO
from typing import Union

from flask import url_for, session, flash
from flask_babel import gettext as _
from flask_login import current_user
import pyotp
import qrcode

import config
from pgadmin.model import UserMFA

from .registry import BaseMFAuth
from .utils import ValidationException, fetch_auth_option, mfa_add


_TOTP_AUTH_METHOD = "authenticator"
_TOTP_AUTHENTICATOR = _("Authenticator App")


class TOTPAuthenticator(BaseMFAuth):
    """
    Authenction class for TOTP based authentication.

    Base Class: BaseMFAuth
    """

    @classmethod
    def __create_topt_for_currentuser(cls) -> pyotp.TOTP:
        """
        Create the TOPT object using the secret stored for the current user in
        the configuration database.

        Assumption: Configuration database is not modified by anybody manually,
                    and removed the secrete for the current user.

        Raises:
            ValidationException: Raises when user is not registered for this
                                 authenction method.

        Returns:
            pyotp.TOTP: TOTP object for the current user (if registered)
        """
        options, found = fetch_auth_option(_TOTP_AUTH_METHOD)

        if found is False:
            raise ValidationException(_(
                "User has not registered the Time-based One-Time Password "
                "(TOTP) Authenticator for authentication."
            ))

        if options is None or options == '':
            raise ValidationException(_(
                "User does not have valid HASH to generate the OTP."
            ))

        return pyotp.TOTP(options)

    @property
    def name(self) -> str:
        """
        Name of the authetication method for internal presentation.

        Returns:
            str: Short name for this authentication method
        """
        return _TOTP_AUTH_METHOD

    @property
    def label(self) -> str:
        """
        Label for the UI for this authentication method.

        Returns:
            str: User presentable string for this auth method
        """
        return _(_TOTP_AUTHENTICATOR)

    @property
    def icon(self) -> str:
        """
        Property for the icon url string for this auth method, to be used on
        the authentication or registration page.

        Returns:
            str: url for the icon representation for this auth method
        """
        return url_for("mfa.static", filename="images/totp_lock.svg")

    def validate(self, **kwargs):
        """
        Validate the code sent using the HTTP request.

        Raises:
            ValidationException: Raises when code is not valid
        """
        code = kwargs.get('code')
        totp = TOTPAuthenticator.__create_topt_for_currentuser()

        if totp.verify(code) is False:
            raise ValidationException("Invalid Code")

    def validation_view(self) -> str:
        """
        Generate the portion of the view to render on the authentication page

        Returns:
            str: Authentication view as a string
        """
        return (
            "<div class='form-group'>{auth_description}</div>"
            "<div class='form-group'>"
            "  <input class='form-control' placeholder='{otp_placeholder}'"
            "    name='code' type='password' autofocus='' pattern='\\d*'"
            "    autocomplete='one-time-code' require/>"
            "</div>"
        ).format(
            auth_description=_(
                "Enter the code shown in your authenticator application for "
                "TOTP (Time-based One-Time Password)"
            ),
            otp_placeholder=_("Enter code"),
        )

    def _registration_view(self) -> str:
        """
        Internal function to generate a view for the registration page.

        View will contain the QRCode image for the TOTP based authenticator
        applications to scan.

        Returns:
            str: Registration view with QRcode for TOTP based applications
        """

        option = session.pop('mfa_authenticator_opt', None)
        if option is None:
            option = pyotp.random_base32()
        session['mfa_authenticator_opt'] = option
        totp = pyotp.TOTP(option)

        uri = totp.provisioning_uri(
            current_user.username, issuer_name=getattr(
                config, "APP_NAME", "pgAdmin 4"
            )
        )

        img = qrcode.make(uri)
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue())

        return "".join([
            "<h5 class='form-group text-center'>{auth_title}</h5>",
            "<input type='hidden' name='{auth_method}' value='SETUP'/>",
            "<input type='hidden' name='VALIDATE' value='validate'/>",
            "<img src='data:image/jpeg;base64,{image}'" +
            " alt='{qrcode_alt_text}' class='w-100'/>",
            "<div class='form-group pt-3'>{auth_description}</div>",
            "<div class='form-group'>",
            "<input class='form-control' " +
            " placeholder='{otp_placeholder}' name='code'" +
            " type='password' autofocus='' autocomplete='one-time-code'" +
            " pattern='\\d*' require>",
            "</div>",
        ]).format(
            auth_title=_(_TOTP_AUTHENTICATOR),
            auth_method=_TOTP_AUTH_METHOD,
            image=img_base64.decode("utf-8"),
            qrcode_alt_text=_("TOTP Authenticator QRCode"),
            auth_description=_(
                "Scan the QR code and the enter the code from the "
                "TOTP Authenticator application"
            ), otp_placeholder=_("Enter code")
        )

    def registration_view(self, form_data) -> Union[str, None]:
        """
        Returns the registration view for this authentication method.

        It is also responsible for validating the code during the registration.

        Args:
            form_data (dict): Form data as a dictionary sent from the
                              registration page for rendering or validation of
                              the code.

        Returns:
            str: Registration view for the 'authenticator' method if it is not
                 a request for the validation of the code or the code sent is
                 not a valid TOTP code, otherwise - it will return None.
        """

        if 'VALIDATE' not in form_data:
            return self._registration_view()

        code = form_data.get('code', None)
        authenticator_opt = session.get('mfa_authenticator_opt', None)
        if authenticator_opt is None or \
                pyotp.TOTP(authenticator_opt).verify(code) is False:
            flash(_("Failed to validate the code"), "danger")
            return self._registration_view()

        mfa_add(_TOTP_AUTH_METHOD, authenticator_opt)
        flash(_(
            "TOTP Authenticator registered successfully for authentication."
        ), "success")
        session.pop('mfa_authenticator_opt', None)

        return None
