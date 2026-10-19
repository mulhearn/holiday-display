design.pdf: design.tex $(wildcard figures/*.tex)
	latexmk -pdf -interaction=nonstopmode -halt-on-error design.tex

clean:
	latexmk -c design.tex

.PHONY: clean
