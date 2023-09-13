import os, os.path
import sys
import pdf2image

pdf_rasterization_dpi = 500
poppler_path = os.path.abspath(r'.\poppler-22.04.0\Library\bin')

"""
  Rasterizes given pdf to a set of images (one per page)
"""
def convert_pdf_to_images(pdf_path: str, out_dir='.', format='png'):
  try:
    pdf2image.pdfinfo_from_path(pdf_path, poppler_path=poppler_path)
  except Exception as err:
    raise err
  
  dir_path = os.path.splitext(pdf_path)[0]
  if out_dir != None:
    dir_path = os.path.join(out_dir, dir_path)

  if not os.path.exists(dir_path):
    os.mkdir(dir_path)
  pdf2image.convert_from_path(
    pdf_path,
    dpi=pdf_rasterization_dpi,
    output_folder=dir_path,
    fmt=format,
    poppler_path=poppler_path)

if __name__ == '__main__':
  # convert_pdf_to_images(r'in_medias_res.pdf', r'images', format='tiff')
  pdfs_dir = sys.argv[1]
  for file_name in os.listdir(pdfs_dir):
    if file_name == '.' or file_name == '..':
      continue
    if os.path.splitext(file_name)[1] == '.pdf':
      convert_pdf_to_images(os.path.join(pdfs_dir, file_name), format='tiff')