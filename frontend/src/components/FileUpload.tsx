import { useRef, useState } from 'react'

interface Props {
  onFilesChange: (files: File[]) => void
}

export default function FileUpload({ onFilesChange }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [files, setFiles] = useState<File[]>([])
  const [dragging, setDragging] = useState(false)

  const addFiles = (incoming: FileList | null) => {
    if (!incoming) return
    const merged = [...files, ...Array.from(incoming)]
    setFiles(merged)
    onFilesChange(merged)
  }

  const remove = (i: number) => {
    const updated = files.filter((_, idx) => idx !== i)
    setFiles(updated)
    onFilesChange(updated)
  }

  return (
    <div className="w-full">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files) }}
        onClick={() => inputRef.current?.click()}
        className={`border border-dashed rounded-lg px-4 py-3 cursor-pointer transition-all duration-300 flex items-center gap-3
          ${dragging ? 'border-[#00f5ff] bg-[#00f5ff08]' : 'border-[#1a1a2e] hover:border-[#4a4a6a]'}`}
      >
        <span className="text-[#4a4a6a] text-xs tracking-widest">
          {files.length === 0 ? '+ Attach documents (optional)' : `${files.length} file(s) attached`}
        </span>
      </div>
      <input ref={inputRef} type="file" multiple className="hidden" onChange={(e) => addFiles(e.target.files)} />
      {files.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {files.map((f, i) => (
            <span key={i} className="flex items-center gap-1 text-xs bg-[#0f0f1a] border border-[#1a1a2e] rounded px-2 py-1 text-[#4a4a6a]">
              {f.name}
              <button onClick={(e) => { e.stopPropagation(); remove(i) }} className="text-[#bf00ff] hover:text-[#ff006e] ml-1 cursor-pointer">×</button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
