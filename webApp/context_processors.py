"""
Expose social / portfolio URLs to all templates.

Override any default with environment variables in production.
"""
import os


def social_links(request):
    return {
        "social_github_url": os.getenv(
            "SOCIAL_GITHUB_URL",
            "https://github.com/Fez-theblockchain-Dev",
        ),
        "social_linkedin_url": os.getenv(
            "SOCIAL_LINKEDIN_URL",
            "https://www.linkedin.com/in/ramez-festek-0357a51a3",
        ),
        "social_route_url": os.getenv(
            "SOCIAL_ROUTE_URL",
            "https://read.cv/Fez-theblockchain-Dev",
        ),
    }
