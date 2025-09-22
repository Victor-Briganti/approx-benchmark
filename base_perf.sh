NUM_EXEC=9

files=($(ls -1 Performance/2mm/base | sort -V))

write_format () {
    base=$1

    cycles=$(sed -n '6p' Performance/2mm/base/$file | awk '{print $1}' | tr -d ',')
    instruction=$(sed -n '7p' Performance/2mm/base/$file | awk '{print $1}' | tr -d ',')
    seconds=$(sed -n '9p' Performance/2mm/base/$file | awk '{print $1}' | sed -e 's/\./,/g')
    echo $cycles,$instruction,\"$seconds\" >> Evaluation/2mm/base/$base.csv
}


for file in "${files[@]}"; do
    case $file in
        2mm1*)
            write_format "2mm1"
            ;;
        2mm2*)
            write_format "2mm2"
            ;;
        2mm4*)
            write_format "2mm4"
            ;;
        2mm8*)
            write_format "2mm8"
            ;;
        *)
            echo "Something went wrong"
            ;;
    esac
done
