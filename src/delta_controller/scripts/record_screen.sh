#!/usr/bin/env bash
# Quay màn hình để trình chiếu trước hội đồng — mã hóa bằng PHẦN CỨNG của card đồ họa.
#
#   src/delta_controller/scripts/record_screen.sh demo.mp4          # quay tới khi bấm q
#   src/delta_controller/scripts/record_screen.sh demo.mp4 60       # quay đúng 60 giây
#   GEOMETRY=1280x720+320+180 src/.../record_screen.sh demo.mp4     # chỉ quay một vùng
#
# VÌ SAO BẢN QUAY TRƯỚC BỊ GIẬT: bộ quay màn hình tích hợp nén VP8 bằng CPU, trong khi CPU đang
# bận chạy Gazebo và khối thị giác. Đo trên tệp cũ: 396 khung trong 70,8 s (5,6 hình/s, mất 81 %
# số khung), có lúc đứng hẳn 2,7 giây. Chương trình chạy mượt; thứ không theo kịp là bộ mã hóa.
#
# BA THAY ĐỔI, mỗi thứ sửa một nguyên nhân:
#   1. NVENC — mã hóa chạy trên khối phần cứng riêng của card, không tranh CPU với Gazebo, cũng
#      không tranh nhân đồ họa đang vẽ cảnh.
#   2. Tốc độ khung CỐ ĐỊNH. Một video đều 25 hình/s trông mượt hơn hẳn video lúc 30 lúc 5 — mắt
#      người bắt khựng chứ không bắt tốc độ. Đây là phần quan trọng nhất.
#   3. Thu nhỏ còn 1280 ngang. Giảm một nửa bề ngang là giảm bốn lần khối lượng nén, và 1280 vẫn
#      thừa nét khi chiếu máy chiếu.
set -euo pipefail

OUT="${1:-demo.mp4}"
SECONDS_LIMIT="${2:-}"
FPS="${FPS:-25}"
GEOMETRY="${GEOMETRY:-}"
SCALE_W="${SCALE_W:-1280}"
DISPLAY_NUM="${DISPLAY:-:0}"

if [ -z "$GEOMETRY" ]; then
  GEOMETRY="$(xrandr 2>/dev/null | awk '/\*/{print $1; exit}')+0+0"
fi
SIZE="${GEOMETRY%%+*}"
OFFSET="${GEOMETRY#*"$SIZE"}"

# Chọn bộ mã hóa tốt nhất đang có. Thứ tự: card rời -> chip Intel -> CPU (phương án cuối).
if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q h264_nvenc && nvidia-smi >/dev/null 2>&1; then
  ENC=(-c:v h264_nvenc -preset p4 -tune hq -rc vbr -cq 23 -b:v 8M -maxrate 12M)
  WHICH='NVENC (card roi)'
elif ffmpeg -hide_banner -encoders 2>/dev/null | grep -q h264_vaapi && [ -e /dev/dri/renderD128 ]; then
  ENC=(-vaapi_device /dev/dri/renderD128 -vf 'format=nv12,hwupload' -c:v h264_vaapi -b:v 8M)
  WHICH='VAAPI (chip Intel)'
else
  ENC=(-c:v libx264 -preset ultrafast -crf 23)
  WHICH='libx264 (CPU — se nang may, chi dung khi khong con cach khac)'
fi

LIMIT=()
[ -n "$SECONDS_LIMIT" ] && LIMIT=(-t "$SECONDS_LIMIT")

echo "Quay $SIZE tai $OFFSET -> $OUT"
echo "  bo ma hoa: $WHICH"
echo "  toc do khung CO DINH: $FPS hinh/s, thu nho con ${SCALE_W} ngang"
[ -n "$SECONDS_LIMIT" ] && echo "  dung sau $SECONDS_LIMIT giay" || echo "  bam q de dung"

ffmpeg -hide_banner -loglevel warning -stats \
  -f x11grab -framerate "$FPS" -video_size "$SIZE" -i "${DISPLAY_NUM}${OFFSET}" \
  "${LIMIT[@]}" \
  -vf "scale=${SCALE_W}:-2" \
  "${ENC[@]}" -pix_fmt yuv420p -g "$((FPS * 2))" \
  -movflags +faststart -y "$OUT"

echo
echo "Xong: $OUT"
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,avg_frame_rate,nb_frames \
  -show_entries format=duration,size -of default=noprint_wrappers=1 "$OUT"
