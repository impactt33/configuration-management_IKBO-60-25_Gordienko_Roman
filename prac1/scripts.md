## archive.sh

```bash
#!/bin/bash

dir="$1"
tag="$2"
archive_name="$3"

if [ ! -d "$dir" ]; then
  echo "not a directory."
  exit 1
fi

if [ -z "$tag" ]; then
  echo "no parameter"
  exit 1
fi

if [ -z "$archive_name" ]; then
  archive_name="default"
fi


mapfile -t found < <(find "$dir" -type f -name "*.${tag}")


if [ "${#found[@]}" -eq 0 ]; then
  echo "No ${tag} files in this dir."
  exit 0
fi


tar -cvf "${archive_name}.tar" "${found[@]}"
```

## banner.sh

```bash
#!/bin/bash

text="$1"
dashes="+"

for (( i = 0; i < ${#text} + 2; i++ )); do
  dashes="${dashes}-"
done
dashes="${dashes}+"

echo "$dashes"
echo "| $text |"
echo "$dashes"
```

## check_comment.sh

```bash
#!/bin/bash

file="$1"
mask_symb=""

case "$file" in
  *.c)
    mask_symb="(//|/*)"
    ;;
  *.js)
    mask_symb="(//|/*)"
    ;;
  *.py)
    mask_symb="#"
    ;;
  *)
    echo "File is not supported."
    exit 1
    ;;
esac

if [ ! -f "$file" ]; then
  echo "This is not a file."
  exit 1
fi

first_string=$(head -n 1 "$file" | grep -oE "^[${mask_symb}].*")

if [ -z "$first_string" ]; then
  echo "There is no comment in the start."
else
  echo "There is comment in the start."
  echo "$first_string"
fi
```

## empty_files.sh

```bash
#!/bin/bash

dir="$1"

if [ $# -ne 1 ]; then
  echo "params error"
  exit 1
fi

if [ ! -d "$dir" ]; then
  echo "not a directory"
  exit 1
fi

find "$dir" -maxdepth 1 -type f -size 0
```

## find_same.sh

```bash
#!/bin/bash

dir="$1"

if [ ! -d "$dir" ]; then 
  echo "not a directory."
  exit 1
fi

line="$(find "$dir" -type f -exec md5sum {} + | sort | uniq -w 32 --all-repeated=separate)"

if [ -z "$line" ]; then
  echo "No duplicates"
else
  echo "$line"
fi
```

## get_passwd_usrs.sh

```bash
#!/bin/bash

grep -o "^[^:]*" /etc/passwd | sort
```

## identifiers.sh

```bash
#!/bin/bash

file="$1"

if [ $# -eq 0 ]; then
  echo "Не нашел переданных аргументов."
  exit 1
fi

if [ ! -f "$1" ]; then
  echo "$1 не является файлом."
  exit 1
fi

grep -o "[a-zA-Z_][a-zA-Z0-9_]*" $file | tr '\n' ' ' | sort -u
```

## reg.sh

```bash
#!/bin/bash

file="$1"

if [ "$EUID" -ne 0 ]; then 
  echo "Запусти от sudo."
  exit 1
fi

if [ $# -eq 0 ]; then
  echo "Не нашел переданных аргументов."
  exit 1
fi

if [ ! -f "$1" ]; then
  echo "$1 не является файлом."
  exit 1
fi

start_file=$(head -n 1 "$file" | grep -o '^#!')

if [ -z "$start_file" ]; then
  echo "Это не bash script."
  exit 1
fi

dest="/usr/local/bin/$(basename "$file")"

cp "$file" "$dest"
chmod 755 "$dest"

echo "Success"
```

## sort_protocols.sh

```bash
#!/bin/bash

grep -v '^#' /etc/protocols | awk '{print $2, $1}' | sort -nr | head -n 5
```

## space_to_tab.sh

```bash
#!/bin/bash

input_file="$1"
output_file="$2"

if [ $# -ne 2 ]; then
  echo "Usage: $0 input_file output_file"
  exit 1
fi

if [ ! -f "$input_file" ]; then
  echo "$input_file is not a file."
  exit 1
fi

if [ "$input_file" -ef "$output_file" ]; then
  echo "Input and output must be different files."
  exit 1
fi

sed 's/    /\t/g' "$input_file" > "$output_file"
```

