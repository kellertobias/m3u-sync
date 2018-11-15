# wait for mysql to come up
while ! mysqladmin ping -h "127.0.0.1" --silent; do
	sleep 0.1
done

echo "[info] mysql started"

python3 /root/m3usync.py