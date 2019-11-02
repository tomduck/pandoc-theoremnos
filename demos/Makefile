
extensions = .pdf .html .epub .tex

dest = $(addprefix out/demo,$(extensions))


all: $(dest) 


$(filter out/demo.%,$(dest)): demo.md


out/%.pdf: %.md
	@if [ ! -d $(dir $@) ]; then mkdir -p $(dir $@); fi
	pandoc $< --filter pandoc-theoremnos --variable urlcolor=blue -o $@

out/%.html: %.md
	@if [ ! -d $(dir $@) ]; then mkdir -p $(dir $@); fi
	pandoc $< --standalone --filter pandoc-theoremnos --include-in-header=headers/header.html -o $@

out/%.epub: %.md
	@if [ ! -d $(dir $@) ]; then mkdir -p $(dir $@); fi
	pandoc $< -t epub3 --filter pandoc-theoremnos --include-in-header=headers/header.epub -o $@

out/%:
	@if [ ! -d $(dir $@) ]; then mkdir -p $(dir $@); fi
	pandoc $^ --filter pandoc-theoremnos -o $@


restore: clean
	for num in "" ; do \
      for ext in $(extensions) ; do \
        git checkout out/demo$$num$$ext ; \
      done ; \
    done


.PHONY: clean

clean:
	rm -rf out
