username = "leandro"
email = "leandro@gmail.com"
password = "olámundo"

# fields = [{"username": username}, {"email": email}, {"password": password}]
fields = {"username": null, "email": email, "password": password}

# for item in fields:
#     if not item or not item.values:
#         print(f"Erro: O campo {item.keys} precisa ter um valor ")
#         break
#     print(f"{item.keys()} : {item.values()}")

for key, value in fields.items():
    if not value:
        print(f"{key}: O campo {key} precisa ter um valor")
        break
    print(f"{key}: {value}")


# {
#     "username": "leandrogalbarino",
#     "password": "Vma22448812!"
# }
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcwMzMwODA0LCJpYXQiOjE3NzAzMjkwMDQsImp0aSI6IjU3YTYyNDFiYjc1MzQ3M2NiYTk4MmJhNTM5M2YwODQ5IiwidXNlcl9pZCI6Ijc0ODNmOTllLWMyYmYtNGJlMi04NDk4LTM4ZGVjY2NmNjEzNSJ9.xoChYqh690ZncavWsc7-j-iwB1rhK1suAhUOfFnS4WY


# {"username": "leandro", "password": "uma_senha_forte"}
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcwMzMxNDc2LCJpYXQiOjE3NzAzMjk2NzYsImp0aSI6Ijc3Y2NkMmUzMDNhZDQyOWViMDkyMmM2Mzc1NjgyYjhhIiwidXNlcl9pZCI6ImMzZDI2YzIxLTQ4YjQtNGY2YS04MGFmLTYyMTQ2MTRiYWI5OSJ9.Zg4Vq0RX7wwzWTFuIVWPyhSCnvPRqNqWDDqPRBo7MnU