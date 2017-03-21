cd "C:\Users\mvanmaele\Documents\GitHub\gates-model-ui\py\"
for /l %x in (1, 1, 4) do (
	start python gates-model.py %x
)
pause	