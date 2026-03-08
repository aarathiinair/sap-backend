from . import auth, config, users, triggers, report, maintenance, servers, notifications, webhooks, certificates, sap_systems

all_routers = [auth.router, users.router, triggers.router, config.router, report.router, maintenance.router, servers.router, notifications.router, webhooks.router, certificates.router, sap_systems.router]