OAuth2 is a framework for delegated authorization: it lets an application access resources on behalf of a user without ever seeing the user's password. The authorization code flow with PKCE is the recommended flow for browser and mobile applications.

OpenID Connect is a thin identity layer on top of OAuth2. It adds an ID token that tells the application who signed in. LDAP and Active Directory are directories that store users and groups, and an identity provider such as Microsoft Entra ID can sit in front of them to issue the tokens.
