# AWS WAF IP set confugration

Simple CLI tool to add/remove IPs in IP set at AWS WAF

## Install

```bash
git clone
pip install -e .
```

## Usage

### Add

```bash
wafip --ipset=<IP_set_name> add 10.0.0.1
```

### Delete

```bash
wafip --ipset=<IP_set_name> delete 10.0.0.1
```
