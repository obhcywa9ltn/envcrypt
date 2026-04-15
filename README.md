# envcrypt

> A CLI tool for encrypting and syncing `.env` files across team members using age encryption.

---

## Installation

```bash
pip install envcrypt
```

> **Requires:** [age](https://github.com/FiloSottile/age) installed on your system.

---

## Usage

**Encrypt your `.env` file and share it with your team:**

```bash
# Encrypt a .env file for one or more recipients
envcrypt encrypt .env --recipient age1ql3z7hjy... --output .env.age

# Decrypt a received .env file
envcrypt decrypt .env.age --identity ~/.age/key.txt --output .env

# Add a new team member as a recipient
envcrypt add-recipient .env.age --identity ~/.age/key.txt --new-recipient age1xyz...
```

**Typical workflow:**

```bash
# First-time setup
envcrypt init

# Commit the encrypted file, never the plaintext
git add .env.age
git commit -m "chore: update encrypted env"
```

Add `.env` to your `.gitignore` and commit `.env.age` safely to version control.

---

## Configuration

envcrypt looks for a `.envcrypt.toml` file in your project root:

```toml
[recipients]
alice = "age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p"
bob   = "age1lggyhqr..."

[files]
default = ".env"
output  = ".env.age"
```

---

## License

MIT © [envcrypt contributors](https://github.com/your-org/envcrypt)