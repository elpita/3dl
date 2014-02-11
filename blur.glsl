---VERTEX SHADER--- // remember that you should draw a screen aligned quad
varying vec2 vTexCoord;
void main(void)
{
   gl_Position = ftransform();;
  
   // Clean up inaccuracies
   vec2 Pos;
   Pos = sign(gl_Vertex.xy);
 
   gl_Position = vec4(Pos, 0.0, 1.0);
   // Image-space
   vTexCoord = Pos * 0.5 + 0.5;
}

---FRAGMENT SHADER--- // the texture with the scene you want to blur
uniform sampler2D RTScene;
varying vec2 vTexCoord;
const float blurSize = 1.0/512.0; // I've chosen this size because this will result in that every step will be one pixel wide if the RTScene texture is of size 512x512
 
void main(void)
{
   vec4 sum = vec4(0.0);
 
   // blur in y (vertical)
   // take nine samples, with the distance blurSize between them
   sum += texture2D(RTScene, vec2(vTexCoord.x - 4.0*blurSize, vTexCoord.y)) * 0.05;
   sum += texture2D(RTScene, vec2(vTexCoord.x - 3.0*blurSize, vTexCoord.y)) * 0.09;
   sum += texture2D(RTScene, vec2(vTexCoord.x - 2.0*blurSize, vTexCoord.y)) * 0.12;
   sum += texture2D(RTScene, vec2(vTexCoord.x - blurSize, vTexCoord.y)) * 0.15;
   sum += texture2D(RTScene, vec2(vTexCoord.x, vTexCoord.y)) * 0.16;
   sum += texture2D(RTScene, vec2(vTexCoord.x + blurSize, vTexCoord.y)) * 0.15;
   sum += texture2D(RTScene, vec2(vTexCoord.x + 2.0*blurSize, vTexCoord.y)) * 0.12;
   sum += texture2D(RTScene, vec2(vTexCoord.x + 3.0*blurSize, vTexCoord.y)) * 0.09;
   sum += texture2D(RTScene, vec2(vTexCoord.x + 4.0*blurSize, vTexCoord.y)) * 0.05;
 
   gl_FragColor = sum;
}

---VERTEX SHADER--- //
varying vec2 vTexCoord;
 
// remember that you should draw a screen aligned quad
void main(void)
{
   gl_Position = ftransform();;
  
   // Clean up inaccuracies
   vec2 Pos;
   Pos = sign(gl_Vertex.xy);
 
   gl_Position = vec4(Pos, 0.0, 1.0);
   // Image-space
   vTexCoord = Pos * 0.5 + 0.5;
}

---FRAGMENT SHADER--- //
uniform sampler2D RTBlurH; // this should hold the texture rendered by the horizontal blur pass
varying vec2 vTexCoord;
 
const float blurSize = 1.0/512.0;
 
void main(void)
{
   vec4 sum = vec4(0.0);
 
   // blur in y (vertical)
   // take nine samples, with the distance blurSize between them
   sum += texture2D(RTBlurH, vec2(vTexCoord.x, vTexCoord.y - 4.0*blurSize)) * 0.05;
   sum += texture2D(RTBlurH, vec2(vTexCoord.x, vTexCoord.y - 3.0*blurSize)) * 0.09;
   sum += texture2D(RTBlurH, vec2(vTexCoord.x, vTexCoord.y - 2.0*blurSize)) * 0.12;
   sum += texture2D(RTBlurH, vec2(vTexCoord.x, vTexCoord.y - blurSize)) * 0.15;
   sum += texture2D(RTBlurH, vec2(vTexCoord.x, vTexCoord.y)) * 0.16;
   sum += texture2D(RTBlurH, vec2(vTexCoord.x, vTexCoord.y + blurSize)) * 0.15;
   sum += texture2D(RTBlurH, vec2(vTexCoord.x, vTexCoord.y + 2.0*blurSize)) * 0.12;
   sum += texture2D(RTBlurH, vec2(vTexCoord.x, vTexCoord.y + 3.0*blurSize)) * 0.09;
   sum += texture2D(RTBlurH, vec2(vTexCoord.x, vTexCoord.y + 4.0*blurSize)) * 0.05;
 
   gl_FragColor = sum;
}
