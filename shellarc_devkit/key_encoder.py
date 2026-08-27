import os

from cryptography.fernet import Fernet

to_file = str(input("Input the path to your plain secret keys json file : "))
to_file = to_file.strip()

with open(to_file, "r", encoding="utf-8") as f:
    env_file_bi = f.read().encode("utf-8")

key = Fernet.generate_key()
f = Fernet(key)
token = f.encrypt(env_file_bi)

original_key_file_name = os.path.splitext(to_file)[0]
encrypted_token_file = f"{original_key_file_name}_token.bin"
generated_key_file = f"{original_key_file_name}_key.bin"
with open(encrypted_token_file, "wb") as f:
    f.write(token)
with open(generated_key_file, "wb") as f:
    f.write(key)

print(f"Encrypted token file : {encrypted_token_file}")
print(f"Generated key file : {generated_key_file}")
print("------YOUR SECRET KEY <NEVER EXPOSE THE KEY TO ANY UNTRUSTED THIRD PARTIES>------")
print(f"KEY : {key.decode("utf-8")}")
print("------------")