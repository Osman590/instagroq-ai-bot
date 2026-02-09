export const MODES = {
  text:{needImage:false},
  image:{needImage:true},
  removebg:{needImage:true},
  upscale:{needImage:true}
};

let mode=null, file=null;

export function setMode(m){mode=m}
export function setFile(f){file=f}
export function needImage(){return MODES[mode]?.needImage}