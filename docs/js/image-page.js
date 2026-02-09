import {generateImage} from "./image-api.js";
import {setMode, setFile, needImage} from "./image.js";

const screens={
  cards:cards,
  form:form,
  loading:loading,
  result:result
};

function show(n){
  Object.values(screens).forEach(s=>s.classList.remove("active"));
  screens[n].classList.add("active");
}

document.querySelectorAll(".card").forEach(c=>{
  c.onclick=()=>{
    setMode(c.dataset.mode);
    gallery.classList.toggle("hidden",!needImage());
    show("form");
  };
});

back.onclick=()=>show("cards");
gallery.onclick=()=>file.click();
file.onchange=e=>setFile(e.target.files[0]);

generate.onclick=async()=>{
  show("loading");
  const img=await generateImage();
  resultImg.src=img;
  show("result");
};

repeat.onclick=generate.onclick;
close.onclick=()=>show("form");