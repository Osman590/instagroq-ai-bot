export async function generateImage() {
  await new Promise(r=>setTimeout(r,2000));
  return "https://picsum.photos/512";
}