import React, {useState, useEffect} from "react";
import {useParams, useSearchParams } from "react-router-dom"


export const Plan = () => {
    //балуюсь с useState
    const [data, setData] = useState({name: 'nik', age: 29})

    const  changeAge = () => {
        setData({...data, age: 35})
    }

    const  changeName = () => {
        setData({...data, name: "Serg"})
    }

    useEffect(() => { //не вкладывать в функции, в условия, чиклы (никакой вложенности для useEffect)
        console.log(data.age)
        
        return () => {} //Сработает перед удалением компанента
    }, [data.age])

    useEffect(() => { //не вкладывать в функции, в условия, чиклы (никакой вложенности для useEffect)
        console.log(data.name)
    }, [data.name])

    //балуюсь с хуками из Роутинга
    const { demoParam } = useParams()
    const [params,setParams] = useSearchParams()

    useEffect(() => {
        console.log(demoParam)
        setParams({userName:'Sergio', userAge: '97'})
    }, [demoParam,setParams])





    return(
        <>
            <span style={{display: 'block', marginTop: '100px', marginLeft: '100px'}}>{ data.name}</span>
            <span style={{display: 'block', marginTop: '100px', marginLeft: '100px'}}>{ data.age }</span>
            <button onClick={changeAge}>Изменить возраст</button>
            <button onClick={changeName}>Изменить имя </button>


            <span style={{display: 'block', marginTop: '100px', marginLeft: '100px'}}>Имя пользователя - {params.get('userName')}</span>
            <span style={{display: 'block', marginTop: '100px', marginLeft: '100px'}}>Возраст пользователя - { params.get('userAge') }</span>
        </>
    )
}