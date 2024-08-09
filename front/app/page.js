'use client';

import { useState, useRef, useEffect } from "react";

const SERVER_PORT = process.env.SERVER_PORT || 5000;

const BASE_URL = `http://localhost:${SERVER_PORT}`

export default function Home() {
  const [image, setImage] = useState(null);
  const [pickedColor, setPickedColor] = useState(null);
  const [visualCenter, setVisualCenter] = useState(null);
  const canvasRef = useRef(null);
  const [loading, setLoading] = useState(false);

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    setVisualCenter(null);
    setPickedColor(null);


    const formData = new FormData();
    formData.append("image", file);

    const response = await fetch(`${BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
      // Access-Control-Request-Headers
      headers: {
          'Access-Control-Allow-Origin' : '*',
      },
    });


    if (!response.ok) {
      throw new Error("Network response was not ok");
    }

    const data = await response.json();
    

    setImage({url: data.file_url, name: data.file_name});
  };

  /**
   * https://stackoverflow.com/questions/72843899/getboundingclientrec-and-detecting-right-coordinates-on-a-canvas-not-working} event 
   */
  const handleCanvasClick = async (event) => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const rect = canvas.getBoundingClientRect();

    let scaleX = canvas.width / rect.width;   
    let scaleY = canvas.height / rect.height;  // relationship bitmap vs. element for y
  
    const x = (event.clientX - rect.left) * scaleX;
    const y = (event.clientY - rect.top) * scaleY;
  
    // Log coordinates for debugging
    console.log(`Clicked coordinates: (${x}, ${y})`);
  
    const imageData = ctx.getImageData(x, y, 1, 1).data;
    let color = [imageData[0], imageData[1], imageData[2]];
      color.push(
        imageData[3] !== undefined ? imageData[3] : 1
      );
    
  
    // Log color data for debugging
    console.log(`Picked color: rgb(${color[0]}, ${color[1]}, ${color[2]}, ${color[3]})`);
  
    setPickedColor(color);
  };

  const drawVisualCenter = (center) => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const [x, y] = center;

    // Draw horizontal line
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(canvas.width, y);
    ctx.strokeStyle = 'black';
    ctx.lineWidth = 1;
    ctx.stroke();

    // Draw vertical line
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, canvas.height);
    ctx.strokeStyle = 'black';
    ctx.lineWidth = 1;
    ctx.stroke();
  };

  const handleSetTransparency = async () => {
    setLoading(true);
    setVisualCenter(null);
    try {
      console.log(pickedColor)
      const response = await fetch(`${BASE_URL}/apply-transparency`, {
        method: "POST",
        body: JSON.stringify({
          image: image.name,
          color: pickedColor.slice(0, 3)
        }),
        headers: {
          "Content-Type": "application/json"
        }
      })
      if (!response.ok) {
        throw new Error(response.statusText);
      }

      const data = await response.json();

      setPickedColor(null);

      setImage({url: data.file_url, name: data.file_name})
    } catch (error) {
      console.error("Error processing image:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFindVisualCenter = async () => {
    setLoading(true);
    setVisualCenter(null);
    try {
      const response = await fetch(`${BASE_URL}/get-image-center`, {
        method: "POST",
        body: JSON.stringify({
          image: image.name
        }),
        headers: {
          "Content-Type": "application/json"
        }
      });

      const data = await response.json();

      if (!response.ok) {
       
        throw new Error(data.message);
      }

      setVisualCenter(data.center);

      drawVisualCenter(data.center)
    } catch (error) {
      alert(error)
      console.error("Error processing image:", error);

    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (image) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");
      const img = new Image();
      img.src = image.url;
      img.crossOrigin = "Anonymous";
      img.onload = () => {
        canvas.width = img.width;
        canvas.height = img.height;
        
        // make the transparent part visible
        for (let y = 0; y < canvas.height; y += 10) {
          for (let x = 0; x < canvas.width; x += 10) {
            ctx.fillStyle = (x / 10 + y / 10) % 2 === 0 ? '#ccc' : '#fff';
            ctx.fillRect(x, y, 10, 10);
          }
        }

        ctx.drawImage(img, 0, 0);
      };
    }
  }, [image]);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-gray-100 p-4">
      <h1 className="text-3xl font-bold mb-6">Image Processing App</h1>
      <div className="bg-white p-6 rounded-lg shadow-md w-full max-w-md">
      <ol className="list-decimal list-inside space-y-2 text-left mb-4">
          <li className="text-lg">Upload an image</li>
          <li className="text-lg">Click inside the image to pick up a color: this will present the "Set Transparency" button, which when clicked will make the picked color transparent in the image.</li>
          <li className="text-lg">Find the visual center of the image.
          <ul className="list-disc pl-6">
              <li className="mb-2 font-bold">This will only work for images with a transparent background!</li>
              <li className="mb-2">You can use the "Set Transparency" button to make the background transparent.</li>
          </ul>
          </li>
        </ol>

        <input
          type="file"
          accept="image/*"
          onChange={handleImageUpload}
          className="mb-4 w-full"
        />

        {loading && <div className="flex justify-center mb-4">
            <div className="spinner"></div>
          </div>}

        {image && (
          <>
            <canvas
              
              ref={canvasRef}
              onClick={handleCanvasClick}
              className="mb-4 w-full cursor-crosshair"
            />


            {visualCenter && (
              <p className="mt-4 text-center">
                Visual Center: ({visualCenter[0]}, {visualCenter[1]})
              </p>
            )}
            <button
              onClick={handleFindVisualCenter}
              className="bg-blue-500 text-white py-2 px-4 rounded w-full"
              style={{opacity: !loading ? 1 : 0.5}}
              disabled={loading}
            >
              Find Visual Center
            </button>
          </>
        )}

        {pickedColor && (
          <div className="mt-4">
            <h2 className="text-xl font-bold mb-2">Picked Color:</h2>
            <div
              style={{ backgroundColor: `rgba(${pickedColor[0]}, ${pickedColor[1]}, ${pickedColor[2]}, ${pickedColor[3]})` }}
              className="w-full h-10 rounded"
            />
          </div>
        )}

        {<button
          onClick={handleSetTransparency}
          className="mt-4 bg-blue-500 text-white py-2 px-4 rounded w-full"
          // make it less opaque if no color
          style={{opacity: pickedColor && !loading ? 1 : 0.5}}
          disabled={loading || !pickedColor}
        >
          Set Transparency {!pickedColor && "(Pick a color by clicking on the image)"}
        </button>}
      </div>
    </main>
  );
}