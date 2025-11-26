#!/bin/bash
set +xv
# caminho para o diretório PDW
dirPDW="/home/lcarlin/Dropbox/PDW_DRPBX"
dirScript="${dirPDW}"
envBin="/home/lcarlin/pdw/bin"
lastHost="${dirPDW}/LastRunHost.dat"
lockFile="${dirPDW}/$(basename ${dirPDW}/"${0}" sh)lock"
SysOut_File=${dirPDW}/PDW.OUT.TXT
# logFile="${dirPDW}/PDW.lnx.log"

## Verifica se ja está em execução
if [ ! -f "${lockFile}" ]
then 
   echo "PID: $$ | Script: $(basename "${0}") | Host: $(hostname) | When: $(date) " >> "${lockFile}"
else
    echo "ERROR - FATAL - FAIL "
    echo " Processo ja em execução sob o processo $(cat "${lockFile}" )"
    echo "Impossivel de se continuar" 
    exit 9
fi 

# Caminho para o executável do Python que você deseja executar
pythonExe="${envBin}/python"

outLiner=">===================================================================================================================<"

# O nome do .db e do .xlsx tem que ser o mesmo que vem do arquivo "PersonalDataWareHouse.cfg" (ou similar)
pdwDB="$dirPDW/PDW.db"
pdwExcel="$dirPDW/PDW.xlsx"
pythonScript="PersonalDataWareHouse.py"
hostAtual="$(hostname)"

if [ ! -f "$pdwExcel" ] || [ ! -f "$pdwDB" ]; then
    echo "$pdwExcel ou $pdwDB não encontrado"
else
    # [ -f ${logFile} ] && lastRunHost=$(tail -1 ${logFile} | cut -d"|" -f5 | awk '{print $2}' ) || lastRunHost="xxxxxx" 
    # [ ! -z ${lastRunHost} ] && lastRunHost="xxxxxx" 
    if [ ! -f ${lastHost} ]
    then
       lastRunHost="xxxxxx"                                                     
    else 
       lastRunHost="$(cat ${lastHost})"
    fi
    dataCriacaopdwDB=$(stat -c %Y "$pdwDB")
    dataCriacaopdwExcel=$(stat -c %Y "$pdwExcel")
    echo "$outLiner"  | tee -a ${SysOut_File}
    echo "Banco-de-dados    :-> $pdwDB"  | tee -a ${SysOut_File}
    echo "Ultima Atulizacao :-> $(date -d @"$dataCriacaopdwDB" '+%Y-%m-%d %H:%M:%S')"  | tee -a ${SysOut_File}
    echo "$outLiner"  | tee -a ${SysOut_File} 
    echo "Planilha          :-> $pdwExcel"  | tee -a ${SysOut_File}
    echo "Ultima Atulizacao :-> $(date -d @"$dataCriacaopdwExcel" '+%Y-%m-%d %H:%M:%S')"  | tee -a ${SysOut_File} 
    echo "$outLiner"  | tee -a ${SysOut_File}
    echo "Ultimo host       :-> ${lastRunHost} " | tee -a ${SysOut_File}
    echo "host Atual        :-> ${hostAtual} " | tee -a ${SysOut_File}
    echo "$outLiner"  | tee -a ${SysOut_File}
    # Comparar as datas de criação
    if [ "${lastRunHost}" != "${hostAtual}" ] || [ "${dataCriacaopdwExcel}" -gt "${dataCriacaopdwDB}" ] ; then
        source "${envBin}"/activate
        cd "$dirScript" || exit
        # Executa o script Python em segundo plano
        "$pythonExe" "$pythonScript" | tee -a ${SysOut_File} &
        wait $!
        deactivate
        echo "${hostAtual}" >  "${lastHost}"
    else
        echo "A planilha não foi alterada depois da última execução, logo..."  | tee -a ${SysOut_File}
        echo "Não há a necessidade de se executar o Personal Dataware House nesse momento. Verifique mais tarde"  | tee -a ${SysOut_File}
    fi
fi
# Aguarda até que uma tecla seja pressionada antes de encerrar o script
rm -f "${lockFile}"
echo "Pressione qualquer tecla para sair..."
read -r -n 1
