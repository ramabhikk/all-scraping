from random import randint
START = 1000000000000000
END = 9999999999999999

def get_header(csrf):
    return {
            'accept':'application/json',
            'accept-encoding':'gzip, deflate, br',
            'accept-language':'en-GB,en-US;q=0.9,en;q=0.8',
            'content-type':'application/json',
            'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
            'x-csrf-token': csrf,
        }

def get_taxonomy_formdata():
    return {"acceptWaitingRoom": False, "resources": [{"type": "taxonomy", "params": {"includeChildren": True}, "hash": str(randint(START, END))}], "sharedParams": {"includeChildren": True}, "requiresAuthentication": False}


def get_cats_formadata(department, page, referer):
    return {
                "acceptWaitingRoom": True,
                "resources": [
                    {
                    "type": "appState",
                    "params": {},
                    "hash": "8608229003782371"
                    },
                    {
                    "type": "trolleyContents",
                    "params": {},
                    "hash": "2574718136506441"
                    },
                    {
                    "type": "productsByCategory",
                    "params": {
                        "query": {
                        "count": "48",
                        "page": str(page)
                        },
                        "superdepartment": department
                    },
                    "hash": "5809325687081058"
                    }
                ],
                "sharedParams": {
                    "superdepartment": department,
                    "referer": referer,
                    "query": {
                    "count": "48",
                    "page": str(page)
                    }
                },
                "requiresAuthentication": False
                }