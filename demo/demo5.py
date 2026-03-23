from logeye import log, watch, set_path_mode

set_path_mode("project")

log("file = $fpath")
log("relative = $rpath")
log("absolute = $apath")

f = watch(lambda: log("inside lambda"))
f()
