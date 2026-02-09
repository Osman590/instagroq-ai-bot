export async function fakeGenerate(){
  // заглушка, потом заменишь на реальный API
  await new Promise(r=>setTimeout(r, 3000));
  return "https://picsum.photos/512";
}