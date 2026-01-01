$xelatex = 'xelatex -interaction=nonstopmode -file-line-error -halt-on-error %O %S';
$pdf_mode = 5; # Use xelatex
$out_dir = 'build';
ensure_path('TEXINPUTS', './pdf/styles//', './pdf/src//');
$clean_ext = "nav snm toc out fls fdb_latexmk synctex.gz";