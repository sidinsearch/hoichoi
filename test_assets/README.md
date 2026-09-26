# test_assets/

Drop a 30-second slice of any hoichoi video here for an end-to-end smoke test:

```bash
ssh siddharth@100.99.235.46 \
  'ffmpeg -y -i ~/Desktop/hoichoi/resources/bhojon_bilashi.mp4 \
   -ss 0 -t 30 -vf scale=480:-2 \
   -c:v libx264 -preset veryfast -crf 28 -c:a aac -b:a 64k \
   ~/hoichoi_smoke.mp4'

scp siddharth@100.99.235.46:~/hoichoi_smoke.mp4 \
  /home/ubuntu/hoichoi-project/hoichoi/test_assets/smoke.mp4
```

Then:

```bash
curl -F video=@test_assets/smoke.mp4 -F brand_json=@resources/brands.json \
  http://127.0.0.1:8000/api/analyze
```
