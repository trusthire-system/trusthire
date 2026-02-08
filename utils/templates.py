# utils/templates.py
def template_verification_email(name, verification_link):
    return f"""
    <p>Hi <strong>{name}</strong>,</p>
    <p>Click the link below to verify your account:</p>
    <p><a href="{verification_link}">{verification_link}</a></p>
    <p>Thank you!</p>
    """


def template_hr_verification_email(name, verification_link):
    return f"""
    <h2 style="color:#2d6cdf;margin-bottom:10px;">HR Account Approved ✅</h2>
    <p>Hello <strong>{name}</strong>,</p>
    <p>Your HR account has been approved by the Admin.</p>
    <p>Please verify your email to activate your HR dashboard access:</p>

    <p>
        <a href="{verification_link}"
           style="display:inline-block; padding:10px 14px; background:#2d6cdf; color:white;
                  text-decoration:none; border-radius:8px; font-weight:600;">
           Verify HR Email
        </a>
    </p>

    <p style="margin-top:10px;">If the button doesn’t work, use this link:</p>
    <p><a href="{verification_link}">{verification_link}</a></p>

    <p>Thank you,<br/>TrustHire Team</p>
    """


def template_account_approved(name, role):
    return f"""
    <h2 style="color:#2d6cdf;margin-bottom:10px;">Account Approved 🎉</h2>
    <p>Hello <strong>{name}</strong>,</p>
    <p>Congratulations! Your <strong>{role.capitalize()}</strong> account has been successfully verified and activated.</p>
    <p>You can now log in and start using the TrustHire platform.</p>
    """


def template_account_rejected(name, role):
    return f"""
    <h2 style="color:#d9534f;margin-bottom:10px;">Account Rejected ❗</h2>
    <p>Hello <strong>{name}</strong>,</p>
    <p>Unfortunately, your <strong>{role.capitalize()}</strong> account request has been rejected.</p>
    <p>Please review your details and try again, or contact support for clarification.</p>
    """


def template_company_verified(company_name):
    return f"""
    <h2 style="color:#28a745;margin-bottom:10px;">Company Verified ✓</h2>
    <p><strong>{company_name}</strong> has been successfully verified on TrustHire.</p>
    <p>Your HR managers can now activate their accounts and post jobs.</p>
    """


def template_company_rejected(company_name):
    return f"""
    <h2 style="color:#d9534f;margin-bottom:10px;">Company Verification Failed ❗</h2>
    <p>Verification for <strong>{company_name}</strong> has been rejected.</p>
    <p>Please recheck submitted information and try again.</p>
    """
